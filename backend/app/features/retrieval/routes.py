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

from app.core.dependencies import get_retrieval_service
from app.features.authz.request_context import (
    get_current_tenant_record,
    get_current_user_record,
    require_request_context,
)
from app.features.authz.tool_merge import merge_tools
from app.features.retrieval.schemas import (
    RetrievalMessage,
    RetrievalQueryRequest,
    RetrievalQueryResponse,
)
from app.features.retrieval.service import RetrievalService
from app.features.retrieval.tools import resolve_tool

router = APIRouter(dependencies=[Depends(require_request_context)])


def _is_authorized_for_source(data_source: str, tools: list[str]) -> bool:
    data_source = data_source.strip()
    for tool in tools:
        if data_source == tool or data_source.startswith(tool):
            return True
    return False


def _resolve_azure_client(request: Request, model_id: str | None) -> tuple[AsyncAzureOpenAI, str]:
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
    return client, deployment


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
    user_payload = query
    if sources:
        user_payload = f"{query}\n\nSources:\n{sources}"
    history = [
        {"role": message.role, "content": message.content}
        for message in messages
        if message.content
    ]
    payload = [
        {"role": "system", "content": system_prompt},
        *history,
        {"role": "user", "content": user_payload},
    ]
    stream = await client.chat.completions.create(
        model=deployment,
        messages=payload,
        temperature=0.3,
        max_tokens=1024,
        n=1,
        stream=True,
    )
    async for event in stream:
        choice = event.choices[0] if event.choices else None
        delta = choice.delta.content if choice and choice.delta else None
        if not delta:
            continue
        yield delta


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

    mode = payload.mode or (tool.mode if tool else "retrievethenread")
    user_query = payload.query.strip()
    last_user = _extract_last_user_message(payload.messages)
    if last_user:
        user_query = last_user
    search_query = user_query
    if mode == "chatreadretrieveread" and tool and tool.query_prompt:
        client, deployment = _resolve_azure_client(request, payload.model)
        generated = await _generate_search_query(
            client,
            deployment,
            prompt=tool.query_prompt,
            messages=payload.messages,
            query=user_query,
        )
        if generated and generated != "0":
            search_query = generated

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

    retrieval_response = RetrievalQueryResponse(
        provider=provider.id,
        data_source=data_source,
        results=list(results),
    )
    system_prompt = tool.system_prompt if tool else ""
    sources = _format_sources(results, tool.max_result_chars if tool else 1000)
    if mode != "retrievethenread":
        user_query = last_user or user_query

    client, deployment = _resolve_azure_client(request, payload.model)
    message_id = f"msg-{uuid.uuid4()}"
    text_id = "text-1"
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

    async def stream() -> AsyncIterator[AnyStreamEvent]:
        yield StartEvent(messageId=message_id)
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
        yield TextEndEvent(id=text_id)
        yield DataEvent.create(
            "cot",
            {"step": {"id": "answer", "status": "complete"}},
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
