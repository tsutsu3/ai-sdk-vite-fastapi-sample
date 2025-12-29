from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from fastapi_ai_sdk import AIStreamBuilder, create_ai_stream_response

from app.core.dependencies import get_retrieval_service
from app.features.authz.request_context import (
    get_current_tenant_record,
    get_current_user_record,
    require_request_context,
)
from app.features.authz.tool_merge import merge_tools
from app.features.retrieval.schemas import RetrievalQueryRequest, RetrievalQueryResponse
from app.features.retrieval.service import RetrievalService

router = APIRouter(dependencies=[Depends(require_request_context)])


def _is_authorized_for_source(data_source: str, tools: list[str]) -> bool:
    data_source = data_source.strip()
    for tool in tools:
        if data_source == tool or data_source.startswith(tool):
            return True
    return False


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

    tools = merge_tools(tenant_record.default_tools, user_record.tool_overrides)
    if not _is_authorized_for_source(payload.data_source, tools):
        raise HTTPException(status_code=403, detail="Not authorized for this data source.")

    provider = service.resolve_provider(payload.provider)
    if not provider:
        raise HTTPException(status_code=400, detail="Unknown RAG provider.")

    try:
        results = await provider.search(
            payload.query,
            payload.data_source,
            payload.top_k,
            query_embedding=payload.query_embedding,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc

    retrieval_response = RetrievalQueryResponse(
        provider=provider.id,
        data_source=payload.data_source,
        results=list(results),
    )
    builder = AIStreamBuilder()
    builder.start().data("rag", retrieval_response.model_dump(by_alias=True)).finish()

    response: StreamingResponse = create_ai_stream_response(
        builder.build(),
        headers={
            "x-vercel-ai-protocol": "data",
            "Connection": "keep-alive",
        },
    )
    return response
