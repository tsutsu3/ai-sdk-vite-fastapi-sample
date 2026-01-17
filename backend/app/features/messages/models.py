from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class MessagePartRecord(BaseModel):
    """Message part used by the chat UI."""

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    type: Literal["text", "file", "image", "rag-progress", "rag-sources"] = Field(
        description="Part type.",
        examples=["text"],
    )
    text: str | None = Field(
        default=None,
        description="Text content.",
        examples=["Hello"],
    )
    file_id: str | None = Field(
        default=None,
        alias="fileId",
        description="Uploaded file id.",
        examples=["file_abc123"],
    )
    image_id: str | None = Field(
        default=None,
        alias="imageId",
        description="Uploaded image id.",
        examples=["image_abc123"],
    )


class MessageRecord(BaseModel):
    """Chat message with role, parts, and optional model feedback."""

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    id: str = Field(description="Message id.", examples=["msg-001"])
    role: Literal["user", "assistant", "system"] = Field(
        description="Message role.",
        examples=["assistant"],
    )
    parts: list[MessagePartRecord] = Field(description="Message parts.")
    created_at: datetime | None = Field(
        default=None,
        alias="createdAt",
        description="Message timestamp.",
        examples=["2026-01-16T16:21:13.715Z"],
    )
    parent_message_id: str | None = Field(
        default=None,
        alias="parentMessageId",
        description="Parent message id.",
        examples=["msg-000"],
    )
    model_id: str | None = Field(
        default=None,
        alias="modelId",
        description="Model id used for the message.",
        examples=["gpt-4o"],
    )
    reaction: Literal["like", "dislike"] | None = Field(
        default=None,
        description="Reaction metadata.",
        examples=["like"],
    )
