from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.core.dependencies import get_message_repository
from app.features.authz.request_context import (
    get_current_tenant_id,
    get_current_user_id,
    require_request_context,
)
from app.features.messages.ports import MessageRepository
from app.features.messages.models import MessageRecord
from app.features.messages.schemas import (
  MessageReactionRequest,
  MessageReactionResponse,
  MessageResponse,
  MessagesResponse,
)

router = APIRouter(dependencies=[Depends(require_request_context)])


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=MessagesResponse,
    tags=["Messages"],
    summary="List messages",
    description="Lists messages for a conversation.",
    response_description="Message list for the conversation.",
)
async def list_messages(
    request: Request,
    conversation_id: str,
    repo: MessageRepository = Depends(get_message_repository),
    limit: int | None = Query(default=None, ge=1),
    continuation_token: str | None = Query(default=None, alias="continuationToken"),
) -> MessagesResponse:
    """List messages for a conversation.

    Returns the message list in chat-compatible format.
    """
    config = request.app.state.app_config
    max_limit = max(config.messages_page_max_limit, 1)
    default_limit = max(config.messages_page_default_limit, 1)
    resolved_limit = min(limit or default_limit, max_limit)
    messages, next_token = await repo.list_messages(
        get_current_tenant_id(),
        get_current_user_id(),
        conversation_id,
        limit=resolved_limit,
        continuation_token=continuation_token,
        descending=True,
    )
    return MessagesResponse(
        messages=[_to_message_response(message) for message in messages],
        continuation_token=next_token,
    )


@router.patch(
    "/conversations/{conversation_id}/messages/{message_id}",
    response_model=MessageReactionResponse,
    tags=["Messages"],
    summary="Update message reaction",
    description="Updates like/dislike reaction for a message.",
    response_description="Updated message.",
)
async def update_message_reaction(
    conversation_id: str,
    message_id: str,
    payload: MessageReactionRequest,
    repo: MessageRepository = Depends(get_message_repository),
) -> MessageReactionResponse:
    """Update message reaction metadata."""
    updated = await repo.update_message_reaction(
        get_current_tenant_id(),
        get_current_user_id(),
        conversation_id,
        message_id,
        payload.reaction,
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="Message not found")
    return MessageReactionResponse(message=_to_message_response(updated))


def _to_message_response(message: MessageRecord) -> MessageResponse:
    metadata = {}
    if message.model_id:
        metadata["modelId"] = message.model_id
    if message.reaction:
        metadata["reaction"] = message.reaction
    return MessageResponse(
        id=message.id,
        role=message.role,
        parts=message.parts,
        createdAt=message.created_at,
        parentMessageId=message.parent_message_id,
        metadata=metadata or None,
    )
