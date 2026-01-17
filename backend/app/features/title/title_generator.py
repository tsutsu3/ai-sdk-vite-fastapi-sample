from logging import getLogger

from app.core.config import AppConfig
from app.features.chat.run.streamers import ChatStreamer
from app.features.messages.models import MessageRecord
from app.features.title.utils import generate_fallback_title

logger = getLogger(__name__)


class TitleGenerator:
    """Generate conversation titles from chat messages.

    This component encapsulates title generation strategy, using a model when
    configured and falling back to deterministic heuristics when unavailable.
    """

    def __init__(self, config: AppConfig, streamer: ChatStreamer) -> None:
        """Initialize the title generator.

        Args:
            config: Application configuration.
            streamer: Chat streamer implementation.
        """
        self._config = config
        self._streamer = streamer

    async def generate(self, messages: list[MessageRecord]) -> str:
        """Generate a title from the provided chat messages.

        This method prefers the configured model but degrades gracefully to a
        fallback title to keep UI behavior predictable.

        Args:
            messages: Chat messages.

        Returns:
            str: Generated title.
        """
        model_id = self._config.chat_title_model.strip()
        if not model_id:
            logger.warning("Chat title model is not configured; using fallback.")
            return generate_fallback_title(messages)

        try:
            title = await self._streamer.generate_title(messages, model_id)
            logger.info("Generated title using model '%s'", model_id)
        except Exception:
            logger.exception("Failed to generate title using model; using fallback.")
            return generate_fallback_title(messages)

        return title.strip() or generate_fallback_title(messages)
