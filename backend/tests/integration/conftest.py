from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any, Generator

import pytest
from fastapi.testclient import TestClient

from app.core.application import create_app
from app.core.config import Settings
from app.features.authz.service import AuthzService
from app.features.chat.run.service import RunService
from app.features.chat.run.streamers.base import BaseStreamer
from app.features.title.title_generator import TitleGenerator
from app.infra.fixtures.authz.local_data import (
    PROVISIONING,
    TENANTS,
    USER_IDENTITIES,
    USERS,
)
from app.infra.repository.memory.memory_authz_repository import MemoryAuthzRepository
from app.infra.repository.memory.memory_conversations_repository import (
    MemoryConversationRepository,
)
from app.infra.repository.memory.memory_messages_repository import (
    MemoryMessageRepository,
)
from app.infra.repository.memory.memory_usage_repository import MemoryUsageRepository

TESTS_DIR = Path(__file__).parents[1]


class FastTestStreamer(BaseStreamer):
    async def stream_chat(
        self,
        messages: list[dict[str, Any]],
        model_id: str | None,
    ) -> AsyncIterator[str]:
        for token in ("hello", "world"):
            yield token + " "


@pytest.fixture(autouse=True, scope="session")
def patch_settings_env_file_location() -> Generator[None, None, None]:
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setitem(Settings.model_config, "env_file", str(TESTS_DIR / "test-env"))
    yield


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    # monkeypatch.setenv("AUTH_PROVIDER", "local")
    # monkeypatch.setenv("LOCAL_AUTH_USER_EMAIL", "local.user001@example.com")
    # monkeypatch.setenv("CHAT_PROVIDERS", "fake")
    # monkeypatch.setenv("CHAT_DEFAULT_MODEL", "fake-static")
    # monkeypatch.setenv("CHAT_TITLE_MODEL", "fake-static")
    app = create_app()
    with TestClient(app) as client:
        app.state.authz_repository = MemoryAuthzRepository(
            tenants=TENANTS,
            users=USERS,
            user_identities=USER_IDENTITIES,
            provisioning=PROVISIONING,
            delay_max_seconds=0.0,
        )
        app.state.authz_service = AuthzService(app.state.authz_repository)
        app.state.conversation_repository = MemoryConversationRepository()
        app.state.message_repository = MemoryMessageRepository()
        app.state.usage_repository = MemoryUsageRepository()
        app.state.run_service = RunService(
            FastTestStreamer(),
            TitleGenerator(app.state.app_config, FastTestStreamer()),
            chat_runtime=app.state.chat_runtime,
            app_config=app.state.app_config,
        )
        yield client
