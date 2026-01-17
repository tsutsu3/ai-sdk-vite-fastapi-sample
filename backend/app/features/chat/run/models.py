import uuid
from typing import Any

from langchain_core.messages import BaseMessage
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
)

from app.features.messages.models import MessageRecord


class RunRequest(BaseModel):
    """Run request payload for chat execution."""

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    id: str | None = None
    conversation_id: str | None = Field(default=None, alias="conversationId")
    chat_id: str | None = Field(default=None, alias="chatId")
    messages: list[MessageRecord] = Field(default_factory=list)
    model: str | None = None
    tool_id: str | None = Field(default=None, alias="toolId")
    file_ids: list[str] | None = Field(default=None, alias="fileIds")

    @field_validator("messages", mode="before")
    @classmethod
    def _parse_messages(cls, value: Any) -> list[MessageRecord]:
        if not isinstance(value, list):
            return []
        parsed: list[MessageRecord] = []
        for item in value:
            if isinstance(item, MessageRecord):
                parsed.append(item)
                continue
            if not isinstance(item, dict):
                continue
            try:
                payload = dict(item)
                metadata = payload.get("metadata")
                if isinstance(metadata, dict) and "modelId" in metadata:
                    payload["modelId"] = metadata.get("modelId")
                payload["id"] = f"msg-{uuid.uuid4()}"
                parsed.append(MessageRecord.model_validate(payload))
            except ValidationError:
                continue
        return parsed

    @field_validator("file_ids", mode="before")
    @classmethod
    def _parse_file_ids(cls, value: Any) -> list[str] | None:
        if not isinstance(value, list):
            return None
        return [str(item) for item in value]


class StreamContext(BaseModel):
    """Context used during streaming chat execution."""

    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    tenant_id: str
    user_id: str
    conversation_id: str

    message_id: str
    model_id: str | None
    tool_id: str | None = None

    title: str
    should_generate_title: bool

    messages: list[MessageRecord]
    langchain_messages: list[BaseMessage]
