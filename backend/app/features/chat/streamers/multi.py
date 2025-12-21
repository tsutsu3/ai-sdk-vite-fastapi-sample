from collections.abc import AsyncIterator
from typing import Any

from app.features.chat.streamers.base import BaseStreamer, ChatStreamer


class MultiChatStreamer(BaseStreamer):
    def __init__(
        self,
        providers: dict[str, ChatStreamer],
        model_to_provider: dict[str, str],
        default_model_id: str | None = None,
    ) -> None:
        super().__init__()
        self._providers = providers
        self._model_to_provider = model_to_provider
        self._default_model_id = default_model_id

    def _resolve_provider(self, model_id: str | None) -> tuple[str, str]:
        resolved_model = model_id or self._default_model_id
        if not resolved_model:
            raise RuntimeError("Model must be specified.")
        provider = self._model_to_provider.get(resolved_model)
        if not provider:
            raise RuntimeError("Requested model is not available.")
        return provider, resolved_model

    async def stream_chat(
        self,
        messages: list[dict[str, Any]],
        model_id: str | None,
    ) -> AsyncIterator[str]:
        provider, resolved_model = self._resolve_provider(model_id)
        streamer = self._providers.get(provider)
        if not streamer:
            raise RuntimeError("Requested model is not available.")
        async for delta in streamer.stream_chat(messages, resolved_model):
            yield delta

    async def generate_title(
        self,
        messages: list[dict[str, Any]],
        model_id: str | None,
    ) -> str:
        provider, resolved_model = self._resolve_provider(model_id)
        streamer = self._providers.get(provider)
        if not streamer:
            raise RuntimeError("Requested model is not available.")
        return await streamer.generate_title(messages, resolved_model)
