from typing import Any

from app.core.config import AppConfig
from app.features.chat.streamers import ChatStreamer
from app.features.messages.models import ChatMessage
from app.features.title.utils import generate_fallback_title


class TitleGenerator:
    def __init__(self, config: AppConfig, streamer: ChatStreamer) -> None:
        self._config = config
        self._streamer = streamer

    async def generate(self, messages: list[ChatMessage]) -> str:
        model_id = self._config.chat_title_model.strip()
        payload_messages: list[dict[str, Any]] = [
            message.model_dump(by_alias=True, exclude_none=True) for message in messages
        ]
        if not model_id:
            return generate_fallback_title(payload_messages)
        try:
            title = await self._streamer.generate_title(payload_messages, model_id)
        except Exception:
            return generate_fallback_title(payload_messages)
        return title.strip() or generate_fallback_title(payload_messages)
