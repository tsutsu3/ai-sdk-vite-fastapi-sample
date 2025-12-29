from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ChatFileProviderMetadata(BaseModel):
    """File metadata embedded in chat requests."""

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    file_id: str | None = Field(default=None, alias="fileId")


class ChatPartProviderMetadata(BaseModel):
    """Provider metadata embedded in chat requests."""

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    file: ChatFileProviderMetadata | None = None


class ChatMessagePart(BaseModel):
    """Chat message part payload."""

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    type: Literal["text", "file", "image"]
    text: str | None = None
    url: str | None = None
    media_type: str | None = Field(default=None, alias="mediaType")
    filename: str | None = None
    file_id: str | None = Field(default=None, alias="fileId")
    image_id: str | None = Field(default=None, alias="imageId")
    provider_metadata: ChatPartProviderMetadata | None = Field(
        default=None,
        alias="providerMetadata",
    )


class ChatMessageMetadata(BaseModel):
    """Chat message metadata payload."""

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    model_id: str | None = Field(default=None, alias="modelId")
    model_name: str | None = Field(default=None, alias="modelName")


class ChatMessage(BaseModel):
    """Chat message payload."""

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    id: str | None = None
    role: Literal["user", "assistant", "system"]
    parts: list[ChatMessagePart] = Field(default_factory=list)
    parent_message_id: str | None = Field(default=None, alias="parentMessageId")
    created_at: datetime | None = Field(default=None, alias="createdAt")
    metadata: ChatMessageMetadata | None = None


class ChatWebSearchRequest(BaseModel):
    """Web search request configuration."""

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    enabled: bool = False
    engine: str | None = None


class ChatPayload(BaseModel):
    """Chat request payload schema."""

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    id: str | None = None
    conversation_id: str | None = Field(default=None, alias="conversationId")
    chat_id: str | None = Field(default=None, alias="chatId")
    messages: list[ChatMessage] = Field(default_factory=list)
    model: str | None = None
    file_ids: list[str] | None = Field(default=None, alias="fileIds")
    web_search: ChatWebSearchRequest | None = Field(default=None, alias="webSearch")
    web_search_engine: str | None = Field(default=None, alias="webSearchEngine")

    @classmethod
    def from_raw(cls, data: Any) -> "ChatPayload":
        if not isinstance(data, dict):
            return cls()
        if "webSearch" not in data and "websearch" in data:
            data = dict(data)
            data["webSearch"] = data.get("websearch")
        if "webSearchEngine" not in data and "websearchEngine" in data:
            data = dict(data)
            data["webSearchEngine"] = data.get("websearchEngine")
        return cls.model_validate(data)
