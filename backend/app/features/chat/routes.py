from fastapi import APIRouter, Body, Depends
from fastapi.responses import StreamingResponse
from fastapi_ai_sdk import AIStream, create_ai_stream_response

from app.core.dependencies import (
    get_conversation_repository,
    get_message_repository,
    get_run_service,
    get_usage_repository,
)
from app.features.authz.request_context import require_request_context
from app.features.chat.schemas import ChatPayload
from app.features.conversations.ports import ConversationRepository
from app.features.messages.ports import MessageRepository
from app.features.run.models import RunRequest
from app.features.run.service import RunService
from app.features.usage.ports import UsageRepository

router = APIRouter(dependencies=[Depends(require_request_context)])


@router.post(
    "/chat",
    response_class=StreamingResponse,
    tags=["Chat"],
    summary="Stream chat responses",
    description="Streams AI SDK events over Server-Sent Events.",
    response_description="SSE stream of AI SDK events.",
)
async def chat(
    payload: ChatPayload = Body(default_factory=ChatPayload),
    service: RunService = Depends(get_run_service),
    repo: ConversationRepository = Depends(get_conversation_repository),
    message_repo: MessageRepository = Depends(get_message_repository),
    usage_repo: UsageRepository = Depends(get_usage_repository),
) -> StreamingResponse:
    """Stream chat responses using the AI SDK data protocol.

    Returns a Server-Sent Events stream for incremental message delivery.
    """
    run_payload = RunRequest.model_validate(payload.model_dump(by_alias=True, exclude_none=True))
    stream = await service.stream(
        run_payload,
        repo,
        message_repo,
        usage_repo,
    )
    ai_stream = AIStream(stream)

    response: StreamingResponse = create_ai_stream_response(ai_stream)

    return response
