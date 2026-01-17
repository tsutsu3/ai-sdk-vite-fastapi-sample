import logging

from fastapi import APIRouter, Body, Depends, Request
from fastapi.responses import StreamingResponse
from fastapi_ai_sdk import AIStream, create_ai_stream_response

from app.ai.llms.factory import build_chat_model, resolve_chat_model
from app.ai.retrievers.factory import build_retriever_for_provider
from app.core.config import AppConfig, ChatCapabilities
from app.core.dependencies import (
    get_app_config,
    get_chat_capabilities,
    get_conversation_repository,
    get_message_repository,
    get_usage_repository,
)
from app.features.conversations.ports import ConversationRepository
from app.features.messages.ports import MessageRepository
from app.features.retrieval.run.service import build_rag_stream
from app.features.retrieval.schemas import RetrievalQueryRequest
from app.features.usage.ports import UsageRepository
from app.shared.streaming import stream_with_lifecycle

router = APIRouter()
logger = logging.getLogger(__name__)


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
        422: {
            "description": "Validation Error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["body", "query"],
                                "msg": "Field required",
                                "type": "missing",
                            }
                        ]
                    }
                }
            },
        },
        501: {"description": "Retrieval provider is not configured."},
    },
)
async def query_rag(
    request: Request,
    payload: RetrievalQueryRequest = Body(
        ...,
        description="Retrieval query payload.",
        examples=[
            {
                "query": "Summarize the steps",
                "dataSource": "tool01",
                "provider": "memory",
                "model": "gpt-4o",
                "topK": 5,
            }
        ],
    ),
    conversation_repo: ConversationRepository = Depends(get_conversation_repository),
    message_repo: MessageRepository = Depends(get_message_repository),
    usage_repo: UsageRepository = Depends(get_usage_repository),
    app_config: AppConfig = Depends(get_app_config),
    chat_caps: ChatCapabilities = Depends(get_chat_capabilities),
) -> StreamingResponse:
    """Stream retrieval results using the AI SDK data protocol.

    Returns a Server-Sent Events stream containing retrieval results.
    """
    stream = build_rag_stream(
        payload=payload,
        conversation_repo=conversation_repo,
        message_repo=message_repo,
        usage_repo=usage_repo,
        app_config=app_config,
        chat_caps=chat_caps,
        resolver=resolve_chat_model,
        builder=build_chat_model,
        retriever_builder=build_retriever_for_provider,
    )
    guarded_stream = stream_with_lifecycle(
        stream,
        is_disconnected=request.is_disconnected,
        idle_timeout=app_config.stream_idle_timeout_seconds,
        logger=logger,
        stream_name="rag",
    )
    ai_stream = AIStream(guarded_stream)
    response: StreamingResponse = create_ai_stream_response(
        ai_stream,
        headers={
            "x-vercel-ai-protocol": "data",
            "Connection": "keep-alive",
        },
    )
    return response
