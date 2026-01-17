import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.core.dependencies import get_conversation_repository, get_message_repository
from app.features.authz.request_context import (
    get_current_tenant_id,
    get_current_user_id,
)
from app.features.conversations.ports import ConversationRepository
from app.features.messages.models import MessageRecord
from app.features.messages.ports import MessageRepository
from app.features.messages.schemas import (
    MessageReactionRequest,
    MessageReactionResponse,
    MessageResponse,
    MessagesResponse,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=MessagesResponse,
    tags=["Messages"],
    summary="List messages",
    description="Lists messages for a conversation.",
    response_description="Message list for the conversation.",
    responses={
        422: {
            "description": "Validation Error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["query", "limit"],
                                "msg": "Input should be greater than or equal to 1",
                                "type": "greater_than_equal",
                            }
                        ]
                    }
                }
            },
        }
    },
)
async def list_messages(
    request: Request,
    conversation_id: str,
    repo: MessageRepository = Depends(get_message_repository),
    conversation_repo: ConversationRepository = Depends(get_conversation_repository),
    limit: int | None = Query(
        default=None,
        ge=1,
        description="Maximum number of messages to return.",
    ),
    continuation_token: str | None = Query(
        default=None,
        alias="continuationToken",
        description="Continuation token for paging.",
    ),
) -> MessagesResponse:
    """List messages for a conversation.

    Returns the message list in chat-compatible format.
    """
    tenant_id = get_current_tenant_id()
    user_id = get_current_user_id()
    conversation = await conversation_repo.get_conversation(
        tenant_id,
        user_id,
        conversation_id,
    )
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    config = request.app.state.app_config
    max_limit = max(config.messages_page_max_limit, 1)
    default_limit = max(config.messages_page_default_limit, 1)
    resolved_limit = min(limit or default_limit, max_limit)
    messages, next_token = await repo.list_messages(
        tenant_id,
        user_id,
        conversation_id,
        limit=resolved_limit,
        continuation_token=continuation_token,
        descending=True,
    )
    logger.info(
        "messages.listed tenant_id=%s user_id=%s conversation_id=%s count=%d",
        tenant_id,
        user_id,
        conversation_id,
        len(messages),
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
    responses={
        422: {
            "description": "Validation Error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["body", "reaction"],
                                "msg": "Input should be 'like' or 'dislike'",
                                "type": "literal_error",
                            }
                        ]
                    }
                }
            },
        }
    },
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
        logger.warning(
            "messages.reaction.miss tenant_id=%s user_id=%s conversation_id=%s message_id=%s",
            get_current_tenant_id(),
            get_current_user_id(),
            conversation_id,
            message_id,
        )
        raise HTTPException(status_code=404, detail="Message not found")
    logger.info(
        "messages.reaction.updated tenant_id=%s user_id=%s conversation_id=%s message_id=%s reaction=%s",
        get_current_tenant_id(),
        get_current_user_id(),
        conversation_id,
        message_id,
        payload.reaction,
    )
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
