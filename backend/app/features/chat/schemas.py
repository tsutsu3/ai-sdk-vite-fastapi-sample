from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ChatFileProviderMetadata(BaseModel):
    """File metadata embedded in chat requests."""

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    file_id: str | None = Field(
        default=None,
        alias="fileId",
        description="Uploaded file identifier.",
        examples=["file_abc123"],
    )


class ChatPartProviderMetadata(BaseModel):
    """Provider metadata embedded in chat requests."""

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    file: ChatFileProviderMetadata | None = Field(
        default=None,
        description="File metadata for file parts.",
    )


class ChatMessagePart(BaseModel):
    """Chat message part payload."""

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    type: Literal["text", "file", "image"] = Field(
        description="Part type.",
        examples=["text"],
    )
    text: str | None = Field(
        default=None,
        description="Text payload for text parts.",
        examples=["Hello"],
    )
    url: str | None = Field(
        default=None,
        description="External URL for file/image parts.",
    )
    media_type: str | None = Field(
        default=None,
        alias="mediaType",
        description="Media type (MIME).",
        examples=["image/png"],
    )
    filename: str | None = Field(
        default=None,
        description="Original file name.",
    )
    file_id: str | None = Field(
        default=None,
        alias="fileId",
        description="Uploaded file identifier.",
    )
    image_id: str | None = Field(
        default=None,
        alias="imageId",
        description="Uploaded image identifier.",
    )
    provider_metadata: ChatPartProviderMetadata | None = Field(
        default=None,
        alias="providerMetadata",
        description="Provider-specific metadata.",
    )


class ChatMessageMetadata(BaseModel):
    """Chat message metadata payload."""

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    model_id: str | None = Field(
        default=None,
        alias="modelId",
        description="Model identifier used for generation.",
        examples=["gpt-4o"],
    )
    model_name: str | None = Field(
        default=None,
        alias="modelName",
        description="Display name for the model.",
        examples=["GPT-4o"],
    )


class ChatMessage(BaseModel):
    """Chat message payload."""

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    id: str | None = Field(
        default=None,
        description="Message identifier.",
    )
    role: Literal["user", "assistant", "system"] = Field(
        description="Message role.",
        examples=["user"],
    )
    parts: list[ChatMessagePart] = Field(
        default_factory=list,
        description="Message parts in order.",
    )
    parent_message_id: str | None = Field(
        default=None,
        alias="parentMessageId",
        description="Parent message id for threading.",
    )
    created_at: datetime | None = Field(
        default=None,
        alias="createdAt",
        description="Client-side created timestamp.",
    )
    metadata: ChatMessageMetadata | None = Field(
        default=None,
        description="Model and provider metadata.",
    )


class ChatPayload(BaseModel):
    """Chat request payload schema."""

    model_config = ConfigDict(
        frozen=True,
        populate_by_name=True,
        json_schema_extra={
            "examples": [
                {
                    "conversationId": "conv-quickstart",
                    "model": "gpt-4o",
                    "messages": [
                        {
                            "role": "user",
                            "parts": [{"type": "text", "text": "Hello"}],
                        }
                    ],
                }
            ]
        },
    )

    id: str | None = Field(
        default=None,
        description="Client request id.",
    )
    conversation_id: str | None = Field(
        default=None,
        alias="conversationId",
        description="Conversation identifier (preferred).",
    )
    chat_id: str | None = Field(
        default=None,
        alias="chatId",
        description="Legacy conversation id (alias).",
    )
    messages: list[ChatMessage] = Field(
        description="Messages for the current turn.",
    )
    model: str | None = Field(
        default=None,
        description="Target model id.",
        examples=["gpt-4o"],
    )
    file_ids: list[str] | None = Field(
        default=None,
        alias="fileIds",
        description="Uploaded file ids referenced by parts.",
    )

    @classmethod
    def from_raw(cls, data: Any) -> "ChatPayload":
        if not isinstance(data, dict):
            return cls()
        return cls.model_validate(data)
