from typing import Literal

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.features.messages.models import MessagePartRecord, MessageRecord


class MessageMetadataResponse(BaseModel):
    """Metadata payload for message responses."""

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    model_id: str | None = Field(default=None, alias="modelId")
    reaction: Literal["like", "dislike"] | None = None


class MessageResponse(BaseModel):
    """Chat message response payload compatible with the UI."""

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    id: str
    role: Literal["user", "assistant", "system"]
    parts: list[MessagePartRecord]
    created_at: datetime | None = Field(default=None, alias="createdAt")
    parent_message_id: str | None = Field(default=None, alias="parentMessageId")
    metadata: MessageMetadataResponse | None = None


class MessagesResponse(BaseModel):
    """List response for conversation messages."""

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    messages: list[MessageResponse]
    continuation_token: str | None = Field(
        default=None,
        alias="continuationToken",
    )


class MessageReactionRequest(BaseModel):
    """Update request for message reactions."""

    model_config = ConfigDict(frozen=True)

    reaction: Literal["like", "dislike"] | None = None


class MessageReactionResponse(BaseModel):
    """Response payload for message reactions."""

    model_config = ConfigDict(frozen=True)

    message: MessageResponse
