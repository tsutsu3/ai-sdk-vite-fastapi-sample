from collections.abc import AsyncIterator

from fastapi_ai_sdk.models import AnyStreamEvent

from app.ai.ports import RetrieverBuilder
from app.ai.runtime import ChatRuntime
from app.core.config import AppConfig, ChatCapabilities
from app.features.chat.run.chat_execution_service import ChatExecutionService
from app.features.chat.run.models import RunRequest
from app.features.chat.run.persistence_service import PersistenceService
from app.features.chat.run.stream_coordinator import StreamCoordinator
from app.features.chat.run.streamers import ChatStreamer
from app.features.conversations.ports import ConversationRepository
from app.features.messages.ports import MessageRepository
from app.features.title.title_generator import TitleGenerator
from app.features.usage.ports import UsageRepository


class RunService:
    """Facade that wires the run flow services together."""

    def __init__(
        self,
        streamer: ChatStreamer,
        title_generator: TitleGenerator,
        chat_runtime: ChatRuntime | None = None,
        app_config: AppConfig | None = None,
        chat_caps: ChatCapabilities | None = None,
        retriever_builder: RetrieverBuilder | None = None,
    ) -> None:
        self._streamer = streamer
        self._title_generator = title_generator
        self._chat_runtime = chat_runtime
        self._app_config = app_config
        self._chat_caps = chat_caps
        self._retriever_builder = retriever_builder
        # Cache runtimes across requests per model id.
        self._runtime_cache: dict[str, ChatRuntime] = {}

    async def stream(
        self,
        payload: RunRequest,
        conversation_repo: ConversationRepository,
        message_repo: MessageRepository,
        usage_repo: UsageRepository,
    ) -> AsyncIterator[AnyStreamEvent]:
        """Build per-request services and start streaming."""
        persistence = PersistenceService(
            conversation_repo=conversation_repo,
            message_repo=message_repo,
            usage_repo=usage_repo,
        )
        execution = ChatExecutionService(
            message_repo=message_repo,
            chat_runtime=self._chat_runtime,
            app_config=self._app_config,
            chat_caps=self._chat_caps,
            retriever_builder=self._retriever_builder,
            runtime_cache=self._runtime_cache,
        )
        coordinator = StreamCoordinator(
            streamer=self._streamer,
            title_generator=self._title_generator,
            execution=execution,
            persistence=persistence,
        )
        return await coordinator.stream(payload)
