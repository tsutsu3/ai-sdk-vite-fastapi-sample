from fastapi import APIRouter, Depends, Request

from app.dependencies import get_message_repository
from app.features.messages.models import MessagesResponse
from app.features.messages.ports import MessageRepository
from app.shared.request_context import get_tenant_id

router = APIRouter()


@router.get("/conversations/{conversation_id}/messages", response_model=MessagesResponse)
async def list_messages(
    request: Request,
    conversation_id: str,
    repo: MessageRepository = Depends(get_message_repository),
) -> MessagesResponse:
    messages = await repo.list_messages(get_tenant_id(request), conversation_id)
    return MessagesResponse(messages=messages)
