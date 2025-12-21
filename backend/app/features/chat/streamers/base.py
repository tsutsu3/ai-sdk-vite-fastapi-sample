import asyncio
import json
import random
from collections.abc import AsyncIterator
from typing import Any, Protocol

from app.features.title.utils import generate_fallback_title


def sse(payload: dict[str, object]) -> str:
    """Vercel AI SDK DataStream format."""
    return f"data: {json.dumps(payload, separators=(',', ':'))}\n\n"


class ChatStreamer(Protocol):
    def stream_chat(
        self,
        messages: list[dict[str, Any]],
        model_id: str | None,
    ) -> AsyncIterator[str]:
        raise NotImplementedError

    def stream_text_delta(self, delta: str, message_id: str) -> AsyncIterator[str]:
        raise NotImplementedError

    def stream_text_end(self, message_id: str) -> AsyncIterator[str]:
        raise NotImplementedError

    def error_stream(self, message: str) -> AsyncIterator[str]:
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

    async def stream_text_delta(self, delta: str, message_id: str) -> AsyncIterator[str]:
        text_id = "text-1"
        if delta == "":
            return
        if message_id not in self._started:
            self._started.add(message_id)
            yield sse({"type": "start", "messageId": message_id})
            yield sse({"type": "text-start", "id": text_id})
        yield sse({"type": "text-delta", "id": text_id, "delta": delta})

    async def stream_text_end(self, message_id: str) -> AsyncIterator[str]:
        text_id = "text-1"
        yield sse({"type": "text-end", "id": text_id})
        yield sse({"type": "finish", "messageMetadata": {"finishReason": "stop"}})
        yield "data: [DONE]\n\n"

    async def error_stream(self, message: str) -> AsyncIterator[str]:
        payloads = [
            {"type": "error", "errorText": message},
        ]
        for payload in payloads:
            yield f"data: {json.dumps(payload, separators=(',', ':'))}\n\n"
            await asyncio.sleep(random.uniform(0.0, 0.05))
        # yield "data: [DONE]\n\n"

    async def generate_title(
        self,
        messages: list[dict[str, Any]],
        model_id: str | None,
    ) -> str:
        return generate_fallback_title(messages)
