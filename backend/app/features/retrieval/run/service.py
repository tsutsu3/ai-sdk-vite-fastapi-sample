import logging
from collections.abc import AsyncIterator

from fastapi import HTTPException
from fastapi_ai_sdk.models import AnyStreamEvent, DataEvent, StartEvent

from app.ai.models import MemoryPolicy
from app.ai.ports import ChatModelBuilder, ChatModelResolver, RetrieverBuilder
from app.core.config import AppConfig, ChatCapabilities
from app.features.conversations.ports import ConversationRepository
from app.features.messages.ports import MessageRepository
from app.features.retrieval.run import event_builder
from app.features.retrieval.run.execution_service import RetrievalExecutionService
from app.features.retrieval.run.persistence_service import RetrievalPersistenceService
from app.features.retrieval.run.query_planner import QueryPlanner
from app.features.retrieval.run.stream_coordinator import RetrievalStreamCoordinator
from app.features.retrieval.run.utils import truncate_text
from app.features.retrieval.schemas import RetrievalQueryRequest
from app.features.usage.ports import UsageRepository

logger = logging.getLogger(__name__)


def build_rag_stream(
    *,
    payload: RetrievalQueryRequest,
    conversation_repo: ConversationRepository,
    message_repo: MessageRepository,
    usage_repo: UsageRepository,
    app_config: AppConfig,
    chat_caps: ChatCapabilities,
    resolver: ChatModelResolver,
    builder: ChatModelBuilder,
    retriever_builder: RetrieverBuilder,
) -> AsyncIterator[AnyStreamEvent]:
    safe_retriever_builder = _wrap_retriever_builder(retriever_builder)
    memory_policy = MemoryPolicy()
    execution = RetrievalExecutionService(
        app_config=app_config,
        chat_caps=chat_caps,
        resolver=resolver,
        builder=builder,
        retriever_builder=safe_retriever_builder,
        memory_policy=memory_policy,
    )
    planner = QueryPlanner(execution)
    persistence = RetrievalPersistenceService(
        conversation_repo=conversation_repo,
        message_repo=message_repo,
        usage_repo=usage_repo,
    )
    coordinator = RetrievalStreamCoordinator(
        execution=execution,
        persistence=persistence,
    )

    async def stream_generator() -> AsyncIterator[AnyStreamEvent]:
        started = False
        log_context = {
            "conversation_id": payload.chat_id or "",
            "message_id": "",
            "tool_id": payload.tool_id or payload.data_source,
        }
        try:
            auth_ctx = planner.require_auth_context()
            tool_ctx = planner.resolve_tool_context(payload, auth_ctx)
            log_context["tool_id"] = tool_ctx.tool_id_for_conversation
            query_ctx = await planner.resolve_query_context(payload, tool_ctx.tool)
            conversation_ctx = await persistence.ensure_conversation(
                auth_ctx=auth_ctx,
                payload=payload,
                tool_ctx=tool_ctx,
                query_ctx=query_ctx,
            )
            log_context["conversation_id"] = conversation_ctx.conversation_id
            injected_prompt_len = len(payload.injected_prompt) if payload.injected_prompt else 0
            logger.info(
                "rag.query.start conversation_id=%s tool_id=%s provider=%s data_source=%s mode=%s top_k=%s hyde_enabled=%s query_prompt_set=%s query_prompt_used=%s hyde_prompt_set=%s follow_up_prompt_set=%s injected_prompt_set=%s injected_prompt_len=%s history_len=%s user_query_len=%s last_user_message_len=%s search_query_len=%s",
                conversation_ctx.conversation_id,
                tool_ctx.tool_id_for_conversation,
                tool_ctx.provider_id,
                tool_ctx.data_source,
                query_ctx.mode,
                payload.top_k,
                payload.hyde_enabled,
                bool(tool_ctx.tool and tool_ctx.tool.query_prompt),
                bool(
                    tool_ctx.tool
                    and tool_ctx.tool.query_prompt
                    and query_ctx.mode == "chat"
                    and not payload.hyde_enabled
                ),
                bool(tool_ctx.tool and tool_ctx.tool.hyde_prompt),
                bool(tool_ctx.tool and tool_ctx.tool.follow_up_questions_prompt),
                bool(payload.injected_prompt),
                injected_prompt_len,
                len(payload.messages),
                len(query_ctx.user_query) if query_ctx.user_query else 0,
                len(query_ctx.last_user_message) if query_ctx.last_user_message else 0,
                len(query_ctx.search_query) if query_ctx.search_query else 0,
            )

            async for event in coordinator.stream(
                payload=payload,
                auth_ctx=auth_ctx,
                tool_ctx=tool_ctx,
                query_ctx=query_ctx,
                conversation_ctx=conversation_ctx,
                message_repo=message_repo,
            ):
                if isinstance(event, StartEvent):
                    started = True
                    log_context["message_id"] = event.message_id
                elif isinstance(event, DataEvent) and event.type == "data-conversation":
                    conv_id = event.data.get("convId")
                    tool_id = event.data.get("toolId")
                    if conv_id:
                        log_context["conversation_id"] = conv_id
                    if tool_id:
                        log_context["tool_id"] = tool_id
                yield event
        except Exception as exc:
            mapped = _map_exception(exc)
            logger.exception(
                "rag.stream.error conversation_id=%s message_id=%s tool_id=%s detail=%s",
                log_context["conversation_id"],
                log_context["message_id"],
                log_context["tool_id"],
                truncate_text(mapped.detail, 200),
            )
            if started:
                yield event_builder.build_error_event(mapped.detail)
                return
            raise mapped

    return stream_generator()


def _wrap_retriever_builder(retriever_builder: RetrieverBuilder) -> RetrieverBuilder:
    def wrapped(*args, **kwargs):
        try:
            return retriever_builder(*args, **kwargs)
        except RuntimeError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    return wrapped


def _map_exception(exc: Exception) -> HTTPException:
    if isinstance(exc, HTTPException):
        return exc
    if isinstance(exc, ValueError):
        return HTTPException(status_code=400, detail=str(exc))
    if isinstance(exc, RuntimeError):
        return HTTPException(status_code=501, detail=str(exc))
    return HTTPException(status_code=500, detail=str(exc))
