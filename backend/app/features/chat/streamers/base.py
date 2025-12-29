from collections.abc import AsyncIterator
from typing import Protocol

from fastapi_ai_sdk.models import (
    AnyStreamEvent,
    ErrorEvent,
    StartEvent,
    TextDeltaEvent,
    TextEndEvent,
    TextStartEvent,
)

from app.features.messages.models import MessageRecord
from app.features.run.models import OpenAIMessage
from app.features.title.utils import generate_fallback_title


class ChatStreamer(Protocol):
    """Interface for chat streaming implementations.

    This abstraction separates provider-specific streaming from the run
    orchestration layer. Implementations adapt provider responses into
    AI SDK-compatible event streams so the frontend can render incremental
    output consistently.
    """

    def stream_chat(
        self,
        messages: list[OpenAIMessage],
        model_id: str | None,
    ) -> AsyncIterator[str]:
        """Stream raw text deltas from a provider.

        Messages are passed through in provider format, and the streamer
        is responsible for yielding incremental text chunks in order.
        """
        raise NotImplementedError

    def stream_text_delta(self, delta: str, message_id: str) -> AsyncIterator[AnyStreamEvent]:
        """Wrap a text delta into AI SDK stream events.

        The event sequence should be compatible with the UI consumer and
        include message start and text start events as needed.
        """
        raise NotImplementedError

    def stream_text_end(self, message_id: str) -> AsyncIterator[AnyStreamEvent]:
        """Emit end-of-text events for a message.

        This closes the text part for the given message so the UI can
        finalize rendering.
        """
        raise NotImplementedError

    def ensure_message_start(self, message_id: str) -> AnyStreamEvent | None:
        """Ensure a start event is emitted once per message.

        Returns None if the start event has already been emitted.
        """
        raise NotImplementedError

    def error_stream(self, message: str) -> AsyncIterator[AnyStreamEvent]:
        """Emit an error event stream.

        The stream should be compatible with the AI SDK protocol and allow
        the UI to surface a failure state.
        """
        raise NotImplementedError

    async def generate_title(
        self,
        messages: list[MessageRecord],
        model_id: str | None,
    ) -> str:
        """Generate a conversation title.

        This is used when the chat title is not explicitly set and allows
        providers to generate a short summary title.
        """
        raise NotImplementedError


class BaseStreamer(ChatStreamer):
    def __init__(self) -> None:
        self._started: set[str] = set()
        self._text_started: set[str] = set()

    async def stream_text_delta(
        self, delta: str, message_id: str
    ) -> AsyncIterator[AnyStreamEvent]:
        text_id = "text-1"
        if delta == "":
            return
        if message_id not in self._started:
            self._started.add(message_id)
            yield StartEvent(messageId=message_id)
        if message_id not in self._text_started:
            self._text_started.add(message_id)
            yield TextStartEvent(id=text_id)
        yield TextDeltaEvent(id=text_id, delta=delta)

    async def stream_text_end(self, message_id: str) -> AsyncIterator[AnyStreamEvent]:
        text_id = "text-1"
        yield TextEndEvent(id=text_id)

    def ensure_message_start(self, message_id: str) -> AnyStreamEvent | None:
        if message_id in self._started:
            return None
        self._started.add(message_id)
        return StartEvent(messageId=message_id)

    async def error_stream(self, message: str) -> AsyncIterator[AnyStreamEvent]:
        yield ErrorEvent(errorText=message)
        # await asyncio.sleep(random.uniform(0.0, 0.05))

    async def generate_title(
        self,
        messages: list[MessageRecord],
        model_id: str | None,
    ) -> str:
        return generate_fallback_title(messages)
