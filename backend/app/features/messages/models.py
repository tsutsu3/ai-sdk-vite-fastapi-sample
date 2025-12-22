from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class MessagePart(BaseModel):
    model_config = ConfigDict(extra="allow", frozen=True)

    type: str
    text: str | None = None


class MessageMetadata(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True, frozen=True)

    file_ids: list[str] = Field(default_factory=list, alias="fileIds")


class ChatMessage(BaseModel):
    model_config = ConfigDict(extra="allow", frozen=True)

    id: str
    role: Literal["user", "assistant", "system"]
    parts: list[MessagePart]
    metadata: MessageMetadata | None = None


class MessagesResponse(BaseModel, frozen=True):
    messages: list[ChatMessage]
