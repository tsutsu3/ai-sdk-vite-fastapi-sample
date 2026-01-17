from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response

from app.core.dependencies import get_conversation_repository, get_message_repository
from app.features.authz.request_context import (
    get_current_tenant_id,
    get_current_user_id,
)
from app.features.conversations.models import ConversationRecord
from app.features.conversations.ports import ConversationRepository
from app.features.conversations.schemas import (
    ConversationResponse,
    ConversationsResponse,
    ConversationUpdateRequest,
)
from app.features.conversations.service import ConversationService
from app.features.conversations.tenant_scoped import TenantScopedConversationRepository
from app.features.messages.ports import MessageRepository

router = APIRouter()


@router.get(
    "/conversations",
    response_model=ConversationsResponse,
    tags=["Conversations"],
    summary="List conversations",
    description="Lists conversation metadata for the current user.",
    response_description="Conversation metadata list.",
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
async def conversation_history(
    request: Request,
    repo: ConversationRepository = Depends(get_conversation_repository),
    message_repo: MessageRepository = Depends(get_message_repository),
    archived: bool = Query(
        default=False,
        description="Return archived conversations when true.",
    ),
    limit: int | None = Query(
        default=None,
        ge=1,
        description="Maximum number of conversations to return.",
    ),
    continuation_token: str | None = Query(
        default=None,
        alias="continuationToken",
        description="Continuation token for paging.",
    ),
) -> ConversationsResponse:
    """List conversations for the current user.

    Returns conversation metadata only, not full message bodies.
    """
    service = ConversationService(
        TenantScopedConversationRepository(get_current_tenant_id(), repo),
        message_repo,
    )
    config = request.app.state.app_config
    max_limit = max(config.conversations_page_max_limit, 1)
    default_limit = max(config.conversations_page_default_limit, 1)
    resolved_limit = min(limit or default_limit, max_limit)
    if archived:
        conversations, next_token = await service.list_archived_conversations(
            get_current_user_id(),
            limit=resolved_limit,
            continuation_token=continuation_token,
        )
    else:
        conversations, next_token = await service.list_conversations(
            get_current_user_id(),
            limit=resolved_limit,
            continuation_token=continuation_token,
        )
    return ConversationsResponse(conversations=conversations, continuation_token=next_token)


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationResponse,
    tags=["Conversations"],
    summary="Get conversation",
    description="Fetches a single conversation with its messages.",
    response_description="Conversation detail with messages.",
    responses={
        404: {"description": "Conversation not found."},
    },
)
async def conversation_detail(
    conversation_id: str,
    repo: ConversationRepository = Depends(get_conversation_repository),
    message_repo: MessageRepository = Depends(get_message_repository),
) -> ConversationResponse:
    """Fetch a single conversation with messages.

    Returns the message list in chat-compatible format.
    """
    service = ConversationService(
        TenantScopedConversationRepository(get_current_tenant_id(), repo),
        message_repo,
    )
    conversation = await service.get_conversation(
        get_current_user_id(),
        conversation_id,
    )
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return conversation


@router.patch(
    "/conversations",
    response_model=ConversationsResponse,
    tags=["Conversations"],
    summary="Bulk update conversations",
    description="Updates archived status for all conversations.",
    response_description="Updated conversation metadata list.",
    responses={
        400: {
            "description": "Invalid payload. Only archived can be updated in bulk.",
        },
        422: {
            "description": "Validation Error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["body", "archived"],
                                "msg": "Input should be a valid boolean",
                                "type": "bool_parsing",
                            }
                        ]
                    }
                }
            },
        },
    },
)
async def bulk_update_conversations(
    payload: ConversationUpdateRequest,
    repo: ConversationRepository = Depends(get_conversation_repository),
    message_repo: MessageRepository = Depends(get_message_repository),
) -> ConversationsResponse:
    """Update archived status for all conversations.

    Only the archived field is supported for bulk updates.
    """
    if payload.archived is None or payload.title is not None:
        raise HTTPException(status_code=400, detail="Only archived can be updated in bulk.")

    service = ConversationService(
        TenantScopedConversationRepository(get_current_tenant_id(), repo),
        message_repo,
    )
    updated = await service.archive_all_conversations(
        get_current_user_id(),
        archived=payload.archived,
    )
    return ConversationsResponse(conversations=updated)


@router.patch(
    "/conversations/{conversation_id}",
    response_model=ConversationResponse,
    tags=["Conversations"],
    summary="Update conversation",
    description="Updates archived status or title for a conversation.",
    response_description="Updated conversation detail.",
    responses={
        400: {"description": "No updates provided."},
        404: {"description": "Conversation not found."},
        500: {"description": "Failed to update conversation."},
        422: {
            "description": "Validation Error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["body", "title"],
                                "msg": "Input should be a valid string",
                                "type": "string_type",
                            }
                        ]
                    }
                }
            },
        },
    },
)
async def update_conversation(
    conversation_id: str,
    payload: ConversationUpdateRequest,
    repo: ConversationRepository = Depends(get_conversation_repository),
    message_repo: MessageRepository = Depends(get_message_repository),
) -> ConversationResponse:
    """Update a conversation's archived state or title.

    Either archived or title must be provided.
    """
    if payload.archived is None and payload.title is None:
        raise HTTPException(status_code=400, detail="No updates provided")

    scoped_repo = TenantScopedConversationRepository(get_current_tenant_id(), repo)
    user_id = get_current_user_id()

    updated: ConversationRecord | None = None

    if payload.archived is not None:
        updated = await scoped_repo.archive_conversation(
            user_id,
            conversation_id,
            archived=payload.archived,
        )
        if updated is None:
            raise HTTPException(status_code=404, detail="Conversation not found")

    if payload.title is not None:
        updated = await scoped_repo.update_title(
            user_id,
            conversation_id,
            payload.title,
        )
        if updated is None:
            raise HTTPException(status_code=404, detail="Conversation not found")

    if updated is None:
        raise HTTPException(status_code=500, detail="Failed to update conversation")

    messages, _ = await message_repo.list_messages(
        scoped_repo.tenant_id,
        user_id,
        conversation_id,
    )

    return ConversationResponse(
        id=updated.id,
        title=updated.title,
        toolId=updated.toolId,
        archived=updated.archived,
        updatedAt=updated.updatedAt,
        messages=messages,
    )


@router.delete(
    "/conversations/{conversation_id}",
    tags=["Conversations"],
    summary="Delete conversation",
    description="Deletes a conversation and its messages.",
    response_description="No content.",
    status_code=204,
    responses={
        404: {"description": "Conversation not found."},
    },
)
async def delete_conversation(
    conversation_id: str,
    repo: ConversationRepository = Depends(get_conversation_repository),
    message_repo: MessageRepository = Depends(get_message_repository),
) -> Response:
    """Delete a single conversation and its messages.

    Returns 204 on success.
    """
    scoped_repo = TenantScopedConversationRepository(get_current_tenant_id(), repo)
    user_id = get_current_user_id()
    deleted = await scoped_repo.delete_conversation(user_id, conversation_id)
    await message_repo.delete_messages(scoped_repo.tenant_id, user_id, conversation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return Response(status_code=204)


@router.delete(
    "/conversations",
    tags=["Conversations"],
    summary="Delete all conversations",
    description="Deletes all conversations for the current user.",
    response_description="No content.",
    status_code=204,
)
async def delete_all_conversations(
    repo: ConversationRepository = Depends(get_conversation_repository),
    message_repo: MessageRepository = Depends(get_message_repository),
) -> Response:
    """Delete all conversations for the current user.

    Returns 204 on success.
    """
    service = ConversationService(
        TenantScopedConversationRepository(get_current_tenant_id(), repo),
        message_repo,
    )
    await service.delete_all_conversations(get_current_user_id())
    return Response(status_code=204)
