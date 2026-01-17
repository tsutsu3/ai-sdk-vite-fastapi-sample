from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.shared.time import now_datetime


class MessagePartBase(BaseModel):
    model_config = ConfigDict(frozen=True)


class TextPartDoc(MessagePartBase):
    type: Literal["text"]
    text: str


class FilePartDoc(MessagePartBase):
    type: Literal["file"]
    file_id: str = Field(alias="fileId")


class ImagePartDoc(MessagePartBase):
    type: Literal["image"]
    image_id: str = Field(alias="imageId")


class RagProgressPartDoc(MessagePartBase):
    type: Literal["rag-progress"]
    text: str


class RagSourcesPartDoc(MessagePartBase):
    type: Literal["rag-sources"]
    text: str


MessagePartDoc = TextPartDoc | FilePartDoc | ImagePartDoc | RagProgressPartDoc | RagSourcesPartDoc


class MessageDoc(BaseModel):
    """Stored message document representation."""

    model_config = ConfigDict(populate_by_name=True, frozen=True)

    id: str
    tenant_id: str = Field(alias="tenantId")
    tool_id: str = Field(alias="toolId")  # `chat` or tool id ( = tool name)
    user_id: str = Field(alias="userId")
    conversation_id: str = Field(alias="conversationId")
    role: Literal["user", "assistant", "system"]
    parent_message_id: str = Field(default="", alias="parentMessageId")
    parts: list[MessagePartDoc]
    model_id: str | None = Field(default=None, alias="modelId")
    reaction: Literal["like", "dislike"] | None = None
    version: int = 1  # To be used for future migrations
    created_at: datetime = Field(
        default_factory=now_datetime,
        alias="createdAt",
    )
