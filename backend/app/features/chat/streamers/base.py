import asyncio
import random
from collections.abc import AsyncIterator
from typing import Any, Protocol

from app.features.title.utils import generate_fallback_title
from fastapi_ai_sdk.models import (
    AnyStreamEvent,
    ErrorEvent,
    StartEvent,
    TextDeltaEvent,
    TextEndEvent,
    TextStartEvent,
)


class ChatStreamer(Protocol):
    def stream_chat(
        self,
        messages: list[dict[str, Any]],
        model_id: str | None,
    ) -> AsyncIterator[str]:
        raise NotImplementedError

    def stream_text_delta(self, delta: str, message_id: str) -> AsyncIterator[AnyStreamEvent]:
        raise NotImplementedError

    def stream_text_end(self, message_id: str) -> AsyncIterator[AnyStreamEvent]:
        raise NotImplementedError

    def error_stream(self, message: str) -> AsyncIterator[AnyStreamEvent]:
        raise NotImplementedError

    async def generate_title(
        self,
        messages: list[dict[str, Any]],
        model_id: str | None,
    ) -> str:
        raise NotImplementedError


class BaseStreamer(ChatStreamer):
    def __init__(self) -> None:
        self._started: set[str] = set()

    async def stream_text_delta(
        self, delta: str, message_id: str
    ) -> AsyncIterator[AnyStreamEvent]:
        text_id = "text-1"
        if delta == "":
            return
        if message_id not in self._started:
            self._started.add(message_id)
            yield StartEvent(messageId=message_id)
            yield TextStartEvent(id=text_id)
        yield TextDeltaEvent(id=text_id, delta=delta)

    async def stream_text_end(self, message_id: str) -> AsyncIterator[AnyStreamEvent]:
        text_id = "text-1"
        yield TextEndEvent(id=text_id)

    async def error_stream(self, message: str) -> AsyncIterator[AnyStreamEvent]:
        yield ErrorEvent(errorText=message)
        # await asyncio.sleep(random.uniform(0.0, 0.05))

    async def generate_title(
        self,
        messages: list[dict[str, Any]],
        model_id: str | None,
    ) -> str:
        return generate_fallback_title(messages)
