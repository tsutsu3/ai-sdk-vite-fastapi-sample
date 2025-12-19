from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.dependencies import get_chat_stream_service
from app.features.chat.stream_service import ChatStreamService

router = APIRouter()


@router.post("/api/chat", response_class=StreamingResponse)
def chat(
    service: ChatStreamService = Depends(get_chat_stream_service),
) -> StreamingResponse:
    response = StreamingResponse(
        service.stream(),
        media_type="text/event-stream",
    )

    response.headers["x-vercel-ai-ui-message-stream"] = "v1"
    response.headers["x-vercel-ai-protocol"] = "data"
    response.headers["Cache-Control"] = "no-cache"
    response.headers["Connection"] = "keep-alive"
    response.headers["X-Accel-Buffering"] = "no"

    return response
