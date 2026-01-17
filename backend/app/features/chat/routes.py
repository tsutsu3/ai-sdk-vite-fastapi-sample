import logging

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi_ai_sdk import AIStream, create_ai_stream_response

from app.core.config import AppConfig
from app.core.dependencies import (
    get_app_config,
    get_conversation_repository,
    get_message_repository,
    get_run_service,
    get_usage_repository,
)
from app.features.chat.run.models import RunRequest
from app.features.chat.run.service import RunService
from app.features.chat.schemas import ChatPayload
from app.features.conversations.ports import ConversationRepository
from app.features.messages.ports import MessageRepository
from app.features.usage.ports import UsageRepository
from app.shared.streaming import stream_with_lifecycle

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/chat",
    response_class=StreamingResponse,
    tags=["Chat"],
    summary="Stream chat responses",
    description=(
        "Streams AI SDK events over Server-Sent Events. "
        "Clients should handle SSE and the AI SDK data protocol."
    ),
    response_description="SSE stream of AI SDK events.",
    responses={
        400: {"description": "Invalid payload."},
        403: {"description": "Unauthorized or forbidden."},
        422: {
            "description": "Validation Error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["body", "messages"],
                                "msg": "Field required",
                                "type": "missing",
                            }
                        ]
                    }
                }
            },
        },
        500: {"description": "Internal error."},
    },
)
async def chat(
    request: Request,
    payload: ChatPayload = Body(
        ...,
        description="Chat request payload.",
        examples=[
            {
                "model": "gpt-4o",
                "messages": [
                    {
                        "role": "user",
                        "parts": [{"type": "text", "text": "Hello"}],
                    }
                ],
            }
        ],
    ),
    service: RunService = Depends(get_run_service),
    repo: ConversationRepository = Depends(get_conversation_repository),
    message_repo: MessageRepository = Depends(get_message_repository),
    usage_repo: UsageRepository = Depends(get_usage_repository),
    app_config: AppConfig = Depends(get_app_config),
) -> StreamingResponse:
    """Stream chat responses using the AI SDK data protocol.

    Returns a Server-Sent Events stream for incremental message delivery.
    """
    if not payload.messages:
        raise HTTPException(status_code=400, detail="Messages are required")
    run_payload = RunRequest.model_validate(payload.model_dump(by_alias=True, exclude_none=True))
    stream = await service.stream(
        run_payload,
        repo,
        message_repo,
        usage_repo,
    )
    stream_idle_timeout = app_config.stream_idle_timeout_seconds

    guarded_stream = stream_with_lifecycle(
        stream,
        is_disconnected=request.is_disconnected,
        idle_timeout=stream_idle_timeout,
        logger=logger,
        stream_name="chat",
    )
    ai_stream = AIStream(guarded_stream)

    response: StreamingResponse = create_ai_stream_response(ai_stream)

    return response
