from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.features.messages.models import MessagePartRecord, MessageRecord


class MessageMetadataResponse(BaseModel):
    """Metadata payload for message responses."""

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    model_id: str | None = Field(
        default=None,
        alias="modelId",
        description="Model id used for the message.",
    )
    reaction: Literal["like", "dislike"] | None = Field(
        default=None,
        description="Reaction metadata.",
    )


class MessageResponse(BaseModel):
    """Chat message response payload compatible with the UI."""

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    id: str = Field(description="Message id.")
    role: Literal["user", "assistant", "system"] = Field(description="Message role.")
    parts: list[MessagePartRecord] = Field(description="Message parts.")
    created_at: datetime | None = Field(
        default=None,
        alias="createdAt",
        description="Message timestamp.",
    )
    parent_message_id: str | None = Field(
        default=None,
        alias="parentMessageId",
        description="Parent message id.",
    )
    metadata: MessageMetadataResponse | None = Field(
        default=None,
        description="Message metadata.",
    )


class MessagesResponse(BaseModel):
    """List response for conversation messages."""

    model_config = ConfigDict(
        frozen=True,
        populate_by_name=True,
        json_schema_extra={
            "examples": [
                {
                    "messages": [
                        {
                            "id": "msg-001",
                            "role": "assistant",
                            "parts": [{"type": "text", "text": "Hello"}],
                            "createdAt": "2026-01-16T16:21:13.715Z",
                            "parentMessageId": "msg-000",
                            "metadata": {"modelId": "gpt-4o"},
                        }
                    ],
                    "continuationToken": "0",
                }
            ]
        },
    )

    messages: list[MessageResponse] = Field(description="Messages list.")
    continuation_token: str | None = Field(
        default=None,
        alias="continuationToken",
        description="Continuation token for paging.",
    )


class MessageReactionRequest(BaseModel):
    """Update request for message reactions."""

    model_config = ConfigDict(
        frozen=True,
        json_schema_extra={
            "examples": [
                {"reaction": "like"},
            ]
        },
    )

    reaction: Literal["like", "dislike"] | None = Field(
        default=None,
        description="Reaction value.",
    )


class MessageReactionResponse(BaseModel):
    """Response payload for message reactions."""

    model_config = ConfigDict(
        frozen=True,
        json_schema_extra={
            "examples": [
                {
                    "message": {
                        "id": "msg-001",
                        "role": "assistant",
                        "parts": [{"type": "text", "text": "Hello"}],
                        "createdAt": "2026-01-16T16:21:13.715Z",
                        "parentMessageId": "msg-000",
                        "metadata": {"modelId": "gpt-4o", "reaction": "like"},
                    }
                }
            ]
        },
    )

    message: MessageResponse = Field(description="Updated message.")
