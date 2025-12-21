from fastapi import APIRouter, Depends

from app.dependencies import get_message_repository
from app.features.messages.models import MessagesResponse
from app.features.messages.ports import MessageRepository
from app.shared.request_context import get_current_tenant_id, require_request_context

router = APIRouter(dependencies=[Depends(require_request_context)])


@router.get("/conversations/{conversation_id}/messages", response_model=MessagesResponse)
async def list_messages(
    conversation_id: str,
    repo: MessageRepository = Depends(get_message_repository),
) -> MessagesResponse:
    messages = await repo.list_messages(get_current_tenant_id(), conversation_id)
    return MessagesResponse(messages=messages)
