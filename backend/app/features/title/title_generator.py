from app.core.config import AppConfig
from app.features.chat.streamers import ChatStreamer
from app.features.title.utils import generate_fallback_title


class TitleGenerator:
    def __init__(self, config: AppConfig, streamer: ChatStreamer) -> None:
        self._config = config
        self._streamer = streamer

    async def generate(self, messages: list[dict]) -> str:
        model_id = self._config.chat_title_model.strip()
        if not model_id:
            return generate_fallback_title(messages)
        try:
            title = await self._streamer.generate_title(messages, model_id)
        except Exception:
            return generate_fallback_title(messages)
        return title.strip() or generate_fallback_title(messages)
