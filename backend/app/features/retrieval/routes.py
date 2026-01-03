import json
import logging
import uuid
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi_ai_sdk import AIStream, create_ai_stream_response
from fastapi_ai_sdk.models import (
    AnyStreamEvent,
    DataEvent,
    SourceURLEvent,
    StartEvent,
    TextDeltaEvent,
    TextEndEvent,
    TextStartEvent,
)
from openai import AsyncAzureOpenAI

from app.core.dependencies import (
    get_conversation_repository,
    get_message_repository,
    get_retrieval_service,
    get_usage_repository,
)
from app.features.authz.request_context import (
    get_current_tenant_id,
    get_current_tenant_record,
    get_current_user_id,
    get_current_user_record,
    require_request_context,
)
from app.features.authz.tool_merge import merge_tools
from app.features.conversations.ports import ConversationRepository
from app.features.messages.models import MessagePartRecord, MessageRecord
from app.features.messages.ports import MessageRepository
from app.features.retrieval.schemas import (
    RetrievalMessage,
    RetrievalQueryRequest,
    RetrievalQueryResponse,
)
from app.features.retrieval.providers.ai_search import AISearchProvider
from app.features.retrieval.providers.local_files import LocalFileRetrievalProvider
from app.features.retrieval.providers.memory import MemoryRetrievalProvider
from app.features.retrieval.providers.postgres import PostgresRetrievalProvider
from app.features.retrieval.service import RetrievalService
from app.features.retrieval.tools import resolve_tool
from app.features.title.utils import generate_fallback_title
from app.features.usage.models import UsageRecord
from app.features.usage.ports import UsageRepository
from app.shared.constants import DEFAULT_CHAT_TITLE
from app.shared.time import now_datetime

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(require_request_context)])


def _is_authorized_for_source(data_source: str, tools: list[str]) -> bool:
    data_source = data_source.strip()
    for tool in tools:
        if data_source == tool or data_source.startswith(tool):
            return True
    return False


def _resolve_azure_client(
    request: Request, model_id: str | None
) -> tuple[AsyncAzureOpenAI, str, str]:
    app_config = request.app.state.app_config
    if not app_config.azure_openai_endpoint or not app_config.azure_openai_api_key:
        raise HTTPException(status_code=501, detail="Azure OpenAI is not configured.")
    deployments = app_config.azure_openai_deployments or {}
    if not deployments:
        raise HTTPException(
            status_code=501, detail="Azure OpenAI deployments are not configured."
        )
    selected_model = model_id or app_config.chat_default_model
    deployment = deployments.get(selected_model) if selected_model else None
    if not deployment:
        deployment = next(iter(deployments.values()))
    client = AsyncAzureOpenAI(
        api_key=app_config.azure_openai_api_key,
        api_version=app_config.azure_openai_api_version,
        azure_endpoint=app_config.azure_openai_endpoint,
    )
    return client, deployment, selected_model or ""


def _resolve_conversation_id(payload: RetrievalQueryRequest) -> str:
    if isinstance(payload.chat_id, str) and payload.chat_id.strip():
        return payload.chat_id.strip()
    return f"conv-{uuid.uuid4()}"


def _extract_last_user_message(messages: list[RetrievalMessage]) -> str:
    for message in reversed(messages):
        if message.role == "user" and message.content.strip():
            return message.content.strip()
    return ""


def _format_sources(results, max_chars: int) -> str:
    lines: list[str] = []
    for index, result in enumerate(results, start=1):
        title = result.title or "Result"
        lines.append(f"{index}. {title}")
        lines.append(f"   URL: {result.url}")
        text = result.text.strip()
        if max_chars > 0 and len(text) > max_chars:
            text = text[: max_chars - 3].rstrip() + "..."
        if text:
            lines.append(f"   Content: {text}")
    return "\n".join(lines)


def _resolve_result_titles(results) -> list[str]:
    titles: list[str] = []
    for result in results:
        title = result.title or result.url
        if title:
            titles.append(title)
    return titles


def _resolve_search_method(provider_id: str, query_embedding: list[float] | None) -> str:
    if query_embedding:
        return "hybrid" if provider_id == "ai-search" else "vector"
    return "keyword"


def _resolve_index_name(provider, data_source: str) -> str:
    if isinstance(provider, LocalFileRetrievalProvider):
        base = provider._base_path  # noqa: SLF001 - debug-only access
        if data_source:
            return str(base / data_source)
        return str(base)
    if isinstance(provider, PostgresRetrievalProvider):
        return provider._table
    return data_source


def _resolve_embedding_model(provider_id: str, query_embedding: list[float] | None) -> str | None:
    if not query_embedding:
        return None
    if provider_id == "postgres":
        return "pgvector"
    return "unknown"


def _resolve_zero_reason(
    *,
    provider,
    provider_id: str,
    data_source: str,
    query: str,
    query_embedding: list[float] | None,
) -> str:
    if not query.strip():
        return "QUERY_TOO_GENERIC"
    if provider_id == "postgres" and not query_embedding:
        return "EMBEDDING_MISMATCH"
    if isinstance(provider, MemoryRetrievalProvider):
        if data_source not in provider._documents:  # noqa: SLF001 - debug-only access
            return "NO_DOCUMENT_IN_INDEX"
    if isinstance(provider, LocalFileRetrievalProvider):
        base = provider._base_path  # noqa: SLF001 - debug-only access
        target = (base / data_source).resolve() if data_source else base.resolve()
        if not target.exists():
            return "NO_DOCUMENT_IN_INDEX"
        if not any(provider._iter_files(data_source)):  # noqa: SLF001 - debug-only access
            return "NO_DOCUMENT_IN_INDEX"
    return "NO_DOCUMENT_IN_INDEX"


def _build_answer_payload(
    *,
    system_prompt: str,
    messages: list[RetrievalMessage],
    query: str,
    sources: str,
) -> list[dict[str, str]]:
    user_payload = query
    if sources:
        user_payload = f"{query}\n\nSources:\n{sources}"
    history = [
        {"role": message.role, "content": message.content}
        for message in messages
        if message.content
    ]
    return [
        {"role": "system", "content": system_prompt},
        *history,
        {"role": "user", "content": user_payload},
    ]


async def _generate_search_query(
    client: AsyncAzureOpenAI,
    deployment: str,
    *,
    prompt: str,
    messages: list[RetrievalMessage],
    query: str,
) -> str:
    history = [
        {"role": message.role, "content": message.content}
        for message in messages
        if message.content
    ]
    payload = [
        {"role": "system", "content": prompt},
        *history,
        {"role": "user", "content": query},
    ]
    response = await client.chat.completions.create(
        model=deployment,
        messages=payload,
        temperature=0.0,
        max_tokens=120,
        n=1,
    )
    content = response.choices[0].message.content if response.choices else None
    if not content:
        return ""
    return content.strip()


async def _stream_answer(
    *,
    client: AsyncAzureOpenAI,
    deployment: str,
    system_prompt: str,
    messages: list[RetrievalMessage],
    query: str,
    sources: str,
) -> AsyncIterator[str]:
    payload = _build_answer_payload(
        system_prompt=system_prompt,
        messages=messages,
        query=query,
        sources=sources,
    )
    stream = await client.chat.completions.create(
        model=deployment,
        messages=payload,
        temperature=0.3,
        max_tokens=1024,
        n=1,
        stream=True,
    )

    buffer = ""
    async for event in stream:
        choice = event.choices[0] if event.choices else None
        delta = choice.delta.content if choice and choice.delta else None
        if delta:
            # Small chunks cause the UI to render everything at once,
            # so we buffer the output to preserve the streaming effect.
            buffer += delta
            if len(buffer) >= 8:
                yield buffer
                buffer = ""

    # Flush any remaining buffer.
    if buffer:
        yield buffer


@router.post(
    "/rag/query",
    response_class=StreamingResponse,
    tags=["RAG"],
    summary="Stream retrieval results",
    description="Streams retrieval results using AI SDK SSE events.",
    response_description="SSE stream of retrieval results.",
    responses={
        400: {"description": "Invalid request or unknown provider."},
        403: {"description": "Not authorized for the requested data source."},
        501: {"description": "Retrieval provider is not configured."},
    },
)
async def query_rag(
    request: Request,
    payload: RetrievalQueryRequest,
    service: RetrievalService = Depends(get_retrieval_service),
    conversation_repo: ConversationRepository = Depends(get_conversation_repository),
    message_repo: MessageRepository = Depends(get_message_repository),
    usage_repo: UsageRepository = Depends(get_usage_repository),
) -> StreamingResponse:
    """Stream retrieval results using the AI SDK data protocol.

    Returns a Server-Sent Events stream containing retrieval results.
    """
    user_record = get_current_user_record()
    tenant_record = get_current_tenant_record()
    if user_record is None or tenant_record is None:
        raise HTTPException(status_code=403, detail="User is not authorized")

    tool = resolve_tool(payload.tool_id)
    data_source = tool.data_source if tool else payload.data_source
    tools = merge_tools(tenant_record.default_tools, user_record.tool_overrides)
    authorize_target = tool.id if tool else data_source
    if not _is_authorized_for_source(authorize_target, tools):
        raise HTTPException(status_code=403, detail="Not authorized for this data source.")

    provider_id = tool.provider if tool and tool.provider else payload.provider
    provider = service.resolve_provider(provider_id)
    if not provider:
        raise HTTPException(status_code=400, detail="Unknown RAG provider.")

    tenant_id = get_current_tenant_id()
    user_id = get_current_user_id()
    conversation_id = _resolve_conversation_id(payload)
    tool_id_for_conversation = (
        tool.id if tool else payload.tool_id if payload.tool_id else data_source or "rag"
    )

    mode = payload.mode or (tool.mode if tool else "retrievethenread")
    user_query = payload.query.strip()
    logger.debug(
        "rag.query.raw provider=%s data_source=%s raw_query=%s",
        provider.id,
        data_source,
        payload.query,
    )
    last_user = _extract_last_user_message(payload.messages)
    if last_user:
        user_query = last_user
    search_query = user_query
    if mode == "chatreadretrieveread" and tool and tool.query_prompt:
        client, deployment, _ = _resolve_azure_client(request, payload.model)
        generated = await _generate_search_query(
            client,
            deployment,
            prompt=tool.query_prompt,
            messages=payload.messages,
            query=user_query,
        )
        if generated and generated != "0":
            search_query = generated

    existing = await conversation_repo.get_conversation(tenant_id, user_id, conversation_id)
    title = existing.title if existing else DEFAULT_CHAT_TITLE
    should_generate_title = not title or title == DEFAULT_CHAT_TITLE
    await conversation_repo.upsert_conversation(
        tenant_id,
        user_id,
        conversation_id,
        title or DEFAULT_CHAT_TITLE,
        tool_id=tool_id_for_conversation,
    )
    user_message_text = last_user or payload.query.strip()
    user_message_id = f"msg-{uuid.uuid4()}" if user_message_text else ""
    last_message_id = ""
    existing_messages, _ = await message_repo.list_messages(
        tenant_id,
        user_id,
        conversation_id,
        limit=1,
        continuation_token=None,
        descending=True,
    )
    if existing_messages:
        last_message_id = existing_messages[0].id
    if user_message_text:
        user_message = MessageRecord(
            id=user_message_id,
            role="user",
            parts=[MessagePartRecord(type="text", text=user_message_text)],
            created_at=now_datetime(),
            parent_message_id=last_message_id,
        )
        await message_repo.upsert_messages(
            tenant_id,
            user_id,
            conversation_id,
            [user_message],
        )

    try:
        results = await provider.search(
            search_query,
            data_source,
            payload.top_k,
            query_embedding=payload.query_embedding,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc
    search_method = _resolve_search_method(provider.id, payload.query_embedding)
    embedding_model = _resolve_embedding_model(provider.id, payload.query_embedding)
    index_name = _resolve_index_name(provider, data_source)
    result_count = len(results)
    logger.debug(
        "rag.query.search provider=%s data_source=%s search_method=%s embedding_model=%s index_name=%s top_k=%s score_threshold=%s result_count=%s",
        provider.id,
        data_source,
        search_method,
        embedding_model,
        index_name,
        payload.top_k,
        None,
        result_count,
    )
    if result_count == 0:
        reason = _resolve_zero_reason(
            provider=provider,
            provider_id=provider.id,
            data_source=data_source,
            query=search_query,
            query_embedding=payload.query_embedding,
        )
        logger.debug(
            "rag.query.zero_results provider=%s data_source=%s reason_code=%s",
            provider.id,
            data_source,
            reason,
        )

    retrieval_response = RetrievalQueryResponse(
        provider=provider.id,
        data_source=data_source,
        results=list(results),
    )
    system_prompt = tool.system_prompt if tool else ""
    sources = _format_sources(results, tool.max_result_chars if tool else 1000)
    if mode != "retrievethenread":
        user_query = last_user or user_query

    client, deployment, selected_model = _resolve_azure_client(request, payload.model)
    message_id = f"msg-{uuid.uuid4()}"
    text_id = "text-1"
    response_text = ""
    sources_payload = [
        {
            "id": f"source-{index}",
            "title": result.title or result.url,
            "url": result.url,
            "description": result.text,
        }
        for index, result in enumerate(results, start=1)
        if result.url
    ]
    result_titles = _resolve_result_titles(results)
    request_payload = _build_answer_payload(
        system_prompt=system_prompt,
        messages=payload.messages,
        query=user_query,
        sources=sources,
    )
    logger.debug(
        "rag.query.answer_payload provider=%s data_source=%s payload=%s",
        provider.id,
        data_source,
        request_payload,
    )
    rag_progress_steps = [
        {
            "id": "search",
            "label": "Search",
            "status": "complete",
            "description": f"Retrieved {len(results)} results.",
            "resultCount": len(results),
            "resultTitles": result_titles,
        },
        {
            "id": "answer",
            "label": "Answer",
            "status": "complete",
            "description": f"Query: {search_query}",
        },
    ]
    generated_title = ""
    if should_generate_title and user_message_text:
        generated_title = generate_fallback_title(
            [
                MessageRecord(
                    id=user_message_id or message_id,
                    role="user",
                    parts=[MessagePartRecord(type="text", text=user_message_text)],
                    created_at=now_datetime(),
                    parent_message_id=last_message_id,
                )
            ]
        )
        if generated_title and generated_title != title:
            await conversation_repo.upsert_conversation(
                tenant_id,
                user_id,
                conversation_id,
                generated_title,
                tool_id=tool_id_for_conversation,
            )

    async def stream() -> AsyncIterator[AnyStreamEvent]:
        nonlocal response_text
        yield StartEvent(messageId=message_id)
        yield DataEvent.create("conversation", {"convId": conversation_id})
        if selected_model:
            yield DataEvent.create("model", {"messageId": message_id, "modelId": selected_model})
        if generated_title:
            yield DataEvent.create("title", {"title": generated_title})
        yield DataEvent.create("rag", retrieval_response.model_dump(by_alias=True))
        yield DataEvent.create(
            "cot",
            {
                "reset": True,
                "open": True,
                "steps": [
                    {"id": "search", "label": "Search", "status": "active"},
                    {"id": "answer", "label": "Answer", "status": "pending"},
                ],
            },
        )
        yield DataEvent.create("sources", {"reset": True, "sources": sources_payload})
        for source in sources_payload:
            yield SourceURLEvent(sourceId=source["id"], url=source["url"])
        yield DataEvent.create(
            "cot",
            {
                "step": {
                    "id": "search",
                    "status": "complete",
                    "description": f"Retrieved {len(results)} results.",
                    "resultCount": len(results),
                    "resultTitles": result_titles,
                }
            },
        )
        yield DataEvent.create(
            "cot",
            {
                "step": {
                    "id": "answer",
                    "status": "active",
                    "description": f"Query: {search_query}",
                }
            },
        )
        yield TextStartEvent(id=text_id)
        async for delta in _stream_answer(
            client=client,
            deployment=deployment,
            system_prompt=system_prompt,
            messages=payload.messages,
            query=user_query,
            sources=sources,
        ):
            yield TextDeltaEvent(id=text_id, delta=delta)
            response_text += delta
        yield TextEndEvent(id=text_id)
        yield DataEvent.create(
            "cot",
            {"step": {"id": "answer", "status": "complete"}},
        )
        assistant_parent_id = user_message_id or last_message_id
        rag_progress_json = json.dumps(rag_progress_steps, ensure_ascii=True)
        rag_sources_json = json.dumps(sources_payload, ensure_ascii=True)
        assistant_message = MessageRecord(
            id=message_id,
            role="assistant",
            parts=[
                MessagePartRecord(type="rag-progress", text=rag_progress_json),
                MessagePartRecord(type="rag-sources", text=rag_sources_json),
                MessagePartRecord(type="text", text=response_text),
            ],
            created_at=now_datetime(),
            parent_message_id=assistant_parent_id,
            model_id=selected_model or None,
        )
        await message_repo.upsert_messages(
            tenant_id,
            user_id,
            conversation_id,
            [assistant_message],
        )
        await usage_repo.record_usage(
            UsageRecord(
                tenant_id=tenant_id,
                user_id=user_id,
                conversation_id=conversation_id,
                message_id=message_id,
                model_id=selected_model or None,
                tokens_in=None,
                tokens_out=None,
                bytes_in=(
                    len(json.dumps(request_payload).encode("utf-8")) if request_payload else None
                ),
                bytes_out=len(response_text.encode("utf-8")) if response_text else None,
                requests=1,
            )
        )

    ai_stream = AIStream(stream())
    response: StreamingResponse = create_ai_stream_response(
        ai_stream,
        headers={
            "x-vercel-ai-protocol": "data",
            "Connection": "keep-alive",
        },
    )
    return response
