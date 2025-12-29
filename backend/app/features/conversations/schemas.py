from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.features.conversations.models import ConversationRecord
from app.features.messages.models import MessageRecord


class ConversationsResponse(BaseModel):
    """List response for conversation metadata."""

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    conversations: list[ConversationRecord]
    continuation_token: str | None = Field(
        default=None,
        alias="continuationToken",
    )


class ConversationResponse(BaseModel):
    """Conversation response with messages."""

    model_config = ConfigDict(frozen=True)

    id: str
    title: str
    messages: list[MessageRecord]
    updatedAt: datetime


class ConversationUpdateRequest(BaseModel):
    """Update payload for conversation changes."""

    model_config = ConfigDict(frozen=True)

    archived: bool | None = None
    title: str | None = None
