from collections.abc import AsyncIterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.core.application import create_app
from app.features.authz.service import AuthzService
from app.features.chat.streamers.base import BaseStreamer
from app.features.retrieval.providers.memory import MemoryRetrievalProvider
from app.features.retrieval.service import RetrievalService
from app.features.run.service import RunService
from app.features.title.title_generator import TitleGenerator
from app.features.web_search.service import WebSearchService
from app.infra.repository.memory.memory_authz_repository import MemoryAuthzRepository
from app.infra.repository.memory.memory_conversations_repository import (
    MemoryConversationRepository,
)
from app.infra.repository.memory.memory_messages_repository import (
    MemoryMessageRepository,
)
from app.infra.repository.memory.memory_usage_repository import MemoryUsageRepository


class FastTestStreamer(BaseStreamer):
    async def stream_chat(
        self,
        messages: list[dict[str, Any]],
        model_id: str | None,
    ) -> AsyncIterator[str]:
        for token in ("hello", "world"):
            yield token + " "


@pytest.fixture()
def client() -> TestClient:
    app = create_app()
    with TestClient(app) as client:
        app.state.authz_repository = MemoryAuthzRepository()
        app.state.authz_service = AuthzService(app.state.authz_repository)
        app.state.conversation_repository = MemoryConversationRepository()
        app.state.message_repository = MemoryMessageRepository()
        app.state.usage_repository = MemoryUsageRepository()
        app.state.retrieval_service = RetrievalService(
            {"memory": MemoryRetrievalProvider()},
            default_provider="memory",
        )
        app.state.web_search_service = WebSearchService(providers={})
        app.state.run_service = RunService(
            FastTestStreamer(),
            TitleGenerator(app.state.app_config, FastTestStreamer()),
            app.state.web_search_service,
            fetch_web_search_content=False,
        )
        yield client
