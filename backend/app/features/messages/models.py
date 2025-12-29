from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class MessagePartRecord(BaseModel):
    """Message part used by the chat UI."""

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    type: Literal["text", "file", "image"]
    text: str | None = None
    file_id: str | None = Field(default=None, alias="fileId")
    image_id: str | None = Field(default=None, alias="imageId")


class MessageRecord(BaseModel):
    """Chat message with role, parts, and optional model feedback."""

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    id: str
    role: Literal["user", "assistant", "system"]
    parts: list[MessagePartRecord]
    created_at: datetime | None = Field(default=None, alias="createdAt")
    parent_message_id: str | None = Field(default=None, alias="parentMessageId")
    model_id: str | None = Field(default=None, alias="modelId")
    reaction: Literal["like", "dislike"] | None = None
