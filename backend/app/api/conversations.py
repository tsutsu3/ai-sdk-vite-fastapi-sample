from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response

from app.dependencies import get_conversation_repository, get_message_repository
from app.features.conversations.models import (
    ConversationResponse,
    ConversationsResponse,
    ConversationUpdateRequest,
)
from app.features.conversations.ports import ConversationRepository
from app.features.conversations.service import ConversationService
from app.features.conversations.tenant_scoped import TenantScopedConversationRepository
from app.features.messages.ports import MessageRepository
from app.shared.request_context import (
    get_current_tenant_id,
    get_current_user_id,
    require_request_context,
)

router = APIRouter(dependencies=[Depends(require_request_context)])


@router.get("/conversations", response_model=ConversationsResponse)
async def conversation_history(
    repo: ConversationRepository = Depends(get_conversation_repository),
    message_repo: MessageRepository = Depends(get_message_repository),
    archived: bool = False,
) -> ConversationsResponse:
    """Return conversation metadata only."""
    service = ConversationService(
        TenantScopedConversationRepository(get_current_tenant_id(), repo),
        message_repo,
    )
    if archived:
        conversations = await service.list_archived_conversations(
            get_current_user_id()
        )
    else:
        conversations = await service.list_conversations(
            get_current_user_id()
        )
    return ConversationsResponse(conversations=conversations)


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationResponse,
)
async def conversation_detail(
    conversation_id: str,
    repo: ConversationRepository = Depends(get_conversation_repository),
    message_repo: MessageRepository = Depends(get_message_repository),
) -> ConversationResponse:
    """Return a single conversation's messages in ai-sdk/useChat format."""
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
    "/conversations/{conversation_id}",
    response_model=ConversationResponse,
)
async def update_conversation(
    conversation_id: str,
    payload: ConversationUpdateRequest,
    repo: ConversationRepository = Depends(get_conversation_repository),
    message_repo: MessageRepository = Depends(get_message_repository),
) -> ConversationResponse:
    if payload.archived is None and payload.title is None:
        raise HTTPException(status_code=400, detail="No updates provided")
    updated_at = datetime.now(timezone.utc).isoformat()
    scoped_repo = TenantScopedConversationRepository(get_current_tenant_id(), repo)
    user_id = get_current_user_id()
    if payload.archived is not None:
        updated = await scoped_repo.archive_conversation(
            user_id,
            conversation_id,
            archived=payload.archived,
            updated_at=updated_at,
        )
        if updated is None:
            raise HTTPException(status_code=404, detail="Conversation not found")
    if payload.title is not None:
        updated = await scoped_repo.update_title(
            user_id,
            conversation_id,
            payload.title,
            updated_at,
        )
        if updated is None:
            raise HTTPException(status_code=404, detail="Conversation not found")
    messages = await message_repo.list_messages(scoped_repo.tenant_id, conversation_id)
    return ConversationResponse(
        id=updated.id,
        title=updated.title,
        updatedAt=updated.updatedAt,
        messages=messages,
    )


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    repo: ConversationRepository = Depends(get_conversation_repository),
    message_repo: MessageRepository = Depends(get_message_repository),
) -> Response:
    scoped_repo = TenantScopedConversationRepository(get_current_tenant_id(), repo)
    user_id = get_current_user_id()
    deleted = await scoped_repo.delete_conversation(user_id, conversation_id)
    await message_repo.delete_messages(scoped_repo.tenant_id, conversation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return Response(status_code=204)


@router.patch("/conversations/archive-all")
async def archive_all_conversations(
    repo: ConversationRepository = Depends(get_conversation_repository),
    message_repo: MessageRepository = Depends(get_message_repository),
) -> Response:
    service = ConversationService(
        TenantScopedConversationRepository(get_current_tenant_id(), repo),
        message_repo,
    )
    await service.archive_all_conversations(get_current_user_id())
    return Response(status_code=204)


@router.delete("/conversations")
async def delete_all_conversations(
    repo: ConversationRepository = Depends(get_conversation_repository),
    message_repo: MessageRepository = Depends(get_message_repository),
) -> Response:
    service = ConversationService(
        TenantScopedConversationRepository(get_current_tenant_id(), repo),
        message_repo,
    )
    await service.delete_all_conversations(get_current_user_id())
    return Response(status_code=204)
