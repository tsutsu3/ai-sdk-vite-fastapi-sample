import logging
from collections.abc import AsyncIterator

from fastapi_ai_sdk.models import AnyStreamEvent, TextDeltaEvent

from app.features.retrieval.run.execution_service import RetrievalExecutionService
from app.features.retrieval.run.longform_pipeline_graph import (
    LongformPipelineState,
    build_longform_pipeline_graph,
    build_longform_pipeline_state,
)
from app.features.retrieval.run.models import (
    AuthContext,
    ConversationContext,
    ToolContext,
)
from app.features.retrieval.run.persistence_service import RetrievalPersistenceService
from app.features.retrieval.run.retrieval_graph import (
    RetrievalPipelineState,
    build_retrieval_graph,
    build_retrieval_state,
)
from app.features.retrieval.run.utils import truncate_text, uuid4_str
from app.features.retrieval.schemas import RetrievalQueryRequest

logger = logging.getLogger(__name__)


class RetrievalStreamCoordinator:
    """Control event ordering and stream flow for RAG responses."""

    def __init__(
        self,
        *,
        execution: RetrievalExecutionService,
        persistence: RetrievalPersistenceService,
        chapter_concurrency: int,
    ) -> None:
        self._persistence = persistence
        self._longform_graph = build_longform_pipeline_graph(
            execution=execution,
            persistence=persistence,
            chapter_concurrency=chapter_concurrency,
        )
        self._retrieval_graph = build_retrieval_graph(
            execution=execution,
            persistence=persistence,
        )

    async def stream(
        self,
        *,
        payload: RetrievalQueryRequest,
        auth_ctx: AuthContext,
        tool_ctx: ToolContext,
        conversation_ctx: ConversationContext,
        message_repo,
    ) -> AsyncIterator[AnyStreamEvent]:
        if payload.pipeline == "longform":
            async for event in self._stream_longform(
                payload=payload,
                auth_ctx=auth_ctx,
                tool_ctx=tool_ctx,
                conversation_ctx=conversation_ctx,
                message_repo=message_repo,
            ):
                yield event
        else:
            async for event in self._stream_default(
                payload=payload,
                auth_ctx=auth_ctx,
                tool_ctx=tool_ctx,
                conversation_ctx=conversation_ctx,
                message_repo=message_repo,
            ):
                yield event

    async def _stream_default(
        self,
        *,
        payload: RetrievalQueryRequest,
        auth_ctx: AuthContext,
        tool_ctx: ToolContext,
        conversation_ctx: ConversationContext,
        message_repo,
    ) -> AsyncIterator[AnyStreamEvent]:
        response_text = ""
        message_id = f"msg-{uuid4_str()}"
        text_id = "text-1"
        retrieval_state = build_retrieval_state(
            payload=payload,
            auth_ctx=auth_ctx,
            tool_ctx=tool_ctx,
            conversation_ctx=conversation_ctx,
            message_repo=message_repo,
            message_id=message_id,
            text_id=text_id,
        )
        state_dict = await self._retrieval_graph.ainvoke(
            retrieval_state.model_dump(mode="python")
        )
        graph_state = RetrievalPipelineState.model_validate(state_dict)
        response_ctx = graph_state.response_ctx
        if response_ctx is None or graph_state.answer_stream is None:
            raise RuntimeError("retrieval graph did not produce expected output")

        for event in graph_state.events:
            yield event

        async for event in graph_state.answer_stream:
            if isinstance(event, TextDeltaEvent):
                response_text += event.delta
            yield event
        logger.debug(
            "rag.query.response_raw provider=%s data_source=%s message_id=%s text=%s",
            tool_ctx.provider_id,
            tool_ctx.data_source,
            message_id,
            truncate_text(response_text, 160),
        )

        await self._persistence.save_messages(
            auth_ctx=auth_ctx,
            conversation_ctx=conversation_ctx,
            response_ctx=response_ctx,
            response_text=response_text,
        )
        await self._persistence.record_usage(
            auth_ctx=auth_ctx,
            conversation_ctx=conversation_ctx,
            response_ctx=response_ctx,
            response_text=response_text,
        )

    async def _stream_longform(
        self,
        *,
        payload: RetrievalQueryRequest,
        auth_ctx: AuthContext,
        tool_ctx: ToolContext,
        conversation_ctx: ConversationContext,
        message_repo,
    ) -> AsyncIterator[AnyStreamEvent]:
        response_text = ""
        message_id = f"msg-{uuid4_str()}"
        text_id = "text-1"
        longform_state = build_longform_pipeline_state(
            payload=payload,
            auth_ctx=auth_ctx,
            tool_ctx=tool_ctx,
            conversation_ctx=conversation_ctx,
            message_repo=message_repo,
            message_id=message_id,
            text_id=text_id,
        )
        state_dict = await self._longform_graph.ainvoke(longform_state.model_dump(mode="python"))
        graph_state = LongformPipelineState.model_validate(state_dict)
        response_ctx = graph_state.response_ctx
        longform_results = graph_state.longform_state
        if response_ctx is None or graph_state.answer_stream is None:
            raise RuntimeError("longform graph did not produce expected output")

        for event in graph_state.events:
            yield event

        if longform_results is not None:
            model_id = response_ctx.selected_model
            await self._persistence.record_usage_entry(
                auth_ctx=auth_ctx,
                conversation_ctx=conversation_ctx,
                message_id=f"msg-{uuid4_str()}",
                model_id=model_id,
                request_payload=longform_results.template_payload,
                response_text=longform_results.template_text,
            )
            for chapter in longform_results.chapter_results:
                await self._persistence.record_usage_entry(
                    auth_ctx=auth_ctx,
                    conversation_ctx=conversation_ctx,
                    message_id=f"msg-{uuid4_str()}",
                    model_id=model_id,
                    request_payload=chapter.request_payload,
                    response_text=chapter.text,
                )
            await self._persistence.record_usage_entry(
                auth_ctx=auth_ctx,
                conversation_ctx=conversation_ctx,
                message_id=f"msg-{uuid4_str()}",
                model_id=model_id,
                request_payload=longform_results.merge_payload,
                response_text=longform_results.merged_text,
            )

        async for event in graph_state.answer_stream:
            if isinstance(event, TextDeltaEvent):
                response_text += event.delta
            yield event

        await self._persistence.record_usage_entry(
            auth_ctx=auth_ctx,
            conversation_ctx=conversation_ctx,
            message_id=message_id,
            model_id=response_ctx.selected_model,
            request_payload=None,
            response_text=response_text,
        )
        logger.debug(
            "rag.longform.response_raw provider=%s data_source=%s message_id=%s text=%s",
            tool_ctx.provider_id,
            tool_ctx.data_source,
            message_id,
            truncate_text(response_text, 160),
        )

        await self._persistence.save_messages(
            auth_ctx=auth_ctx,
            conversation_ctx=conversation_ctx,
            response_ctx=response_ctx,
            response_text=response_text,
        )
