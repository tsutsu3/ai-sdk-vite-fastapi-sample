from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_conversation_repository
from app.features.conversations.models import (
    ConversationResponse,
    ConversationsResponse,
)
from app.features.conversations.repository.conversation_repository import (
    ConversationRepository,
)

router = APIRouter()


@router.get("/api/conversations", response_model=ConversationsResponse)
def conversation_history(
    repo: ConversationRepository = Depends(get_conversation_repository),
) -> ConversationsResponse:
    """Return conversation metadata only."""
    return ConversationsResponse(conversations=repo.list_conversations())


@router.get(
    "/api/conversations/{conversation_id}",
    response_model=ConversationResponse,
)
def conversation_detail(
    conversation_id: str,
    repo: ConversationRepository = Depends(get_conversation_repository),
) -> ConversationResponse:
    """Return a single conversation's messages in ai-sdk/useChat format."""
    conversation = repo.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return conversation
