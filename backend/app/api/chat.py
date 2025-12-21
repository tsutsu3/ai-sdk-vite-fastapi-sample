import json
import uuid
from collections.abc import Iterator

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from app.dependencies import (
    get_conversation_repository,
    get_message_repository,
    get_run_service,
    get_usage_repository,
)
from app.features.conversations.ports import ConversationRepository
from app.features.messages.ports import MessageRepository
from app.features.run.service import RunService
from app.features.usage.ports import UsageRepository
from app.shared.request_context import require_request_context

router = APIRouter(dependencies=[Depends(require_request_context)])


# def error_stream(message: str) -> Iterator[str]:
#     message_id = f"msg-{uuid.uuid4().hex}"
#     payloads = [
#         {"type": "start", "messageId": message_id},
#         {"type": "error", "errorText": message},
#         {"type": "finish", "messageMetadata": {"finishReason": "error"}},
#     ]
#     for payload in payloads:
#         yield f"data: {json.dumps(payload, separators=(',', ':'))}\n\n"
#     yield "data: [DONE]\n\n"


@router.post("/chat", response_class=StreamingResponse)
async def chat(
    request: Request,
    service: RunService = Depends(get_run_service),
    repo: ConversationRepository = Depends(get_conversation_repository),
    message_repo: MessageRepository = Depends(get_message_repository),
    usage_repo: UsageRepository = Depends(get_usage_repository),
) -> StreamingResponse:
    try:
        payload = await request.json()
    except Exception:
        payload = {}

    stream = await service.stream(
        payload,
        repo,
        message_repo,
        usage_repo,
    )

    response = StreamingResponse(stream, media_type="text/event-stream")

    response.headers["x-vercel-ai-ui-message-stream"] = "v1"
    response.headers["x-vercel-ai-protocol"] = "data"
    response.headers["Cache-Control"] = "no-cache"
    response.headers["Connection"] = "keep-alive"
    response.headers["X-Accel-Buffering"] = "no"

    return response
