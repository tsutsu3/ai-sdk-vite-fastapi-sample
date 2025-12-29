from __future__ import annotations

import uuid
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)

from app.features.messages.models import MessageRecord


class OpenAIMessage(BaseModel):
    """OpenAI-style message payload."""

    model_config = ConfigDict(frozen=True)

    role: str
    content: str


class RunRequest(BaseModel):
    """Run request payload for chat execution."""

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    id: str | None = None
    conversation_id: str | None = Field(default=None, alias="conversationId")
    chat_id: str | None = Field(default=None, alias="chatId")
    messages: list[MessageRecord] = Field(default_factory=list)
    model: str | None = None
    file_ids: list[str] | None = Field(default=None, alias="fileIds")
    web_search: WebSearchRequest | None = Field(default=None, alias="webSearch")
    web_search_engine: str | None = Field(default=None, alias="webSearchEngine")

    @model_validator(mode="before")
    @classmethod
    def _normalize_keys(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        if "webSearch" not in data and "websearch" in data:
            data = dict(data)
            data["webSearch"] = data.get("websearch")
        if "webSearchEngine" not in data and "websearchEngine" in data:
            data = dict(data)
            data["webSearchEngine"] = data.get("websearchEngine")
        return data

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


class WebSearchRequest(BaseModel):
    """Web search request configuration."""

    model_config = ConfigDict(frozen=True)

    enabled: bool = False
    engine: str | None = None

    @model_validator(mode="before")
    @classmethod
    def _parse_raw(cls, data: Any) -> Any:
        if isinstance(data, cls):
            return data
        if isinstance(data, bool):
            return {"enabled": data}
        if isinstance(data, str):
            engine = data.strip()
            return {"enabled": True, "engine": engine or None}
        if isinstance(data, dict):
            enabled = bool(data.get("enabled") or data.get("use") or data.get("value"))
            engine_value = data.get("engine") or data.get("id")
            engine = engine_value.strip() if isinstance(engine_value, str) else None
            return {"enabled": enabled, "engine": engine or None}
        return data


class StreamContext(BaseModel):
    """Context used during streaming chat execution."""

    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    tenant_id: str
    user_id: str
    conversation_id: str

    message_id: str
    model_id: str | None

    title: str
    should_generate_title: bool

    messages: list[MessageRecord]
    openai_messages: list[OpenAIMessage]
    web_search: WebSearchRequest = Field(default_factory=WebSearchRequest)
