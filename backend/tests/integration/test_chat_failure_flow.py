from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.core.application import create_app
from app.core.dependencies import get_run_service
from app.features.authz.service import AuthzService
from app.infra.fixtures.authz.local_data import MEMBERSHIPS, TENANTS, USER_IDENTITIES, USERS
from app.infra.repository.memory.memory_authz_repository import MemoryAuthzRepository
from app.infra.repository.memory.memory_conversations_repository import (
    MemoryConversationRepository,
)
from app.infra.repository.memory.memory_messages_repository import (
    MemoryMessageRepository,
)
from app.infra.repository.memory.memory_usage_repository import MemoryUsageRepository


def _build_app():
    return create_app()


def _initialize_state(app) -> None:
    app.state.authz_repository = MemoryAuthzRepository(
        tenants=TENANTS,
        users=USERS,
        user_identities=USER_IDENTITIES,
        memberships=MEMBERSHIPS,
        delay_max_seconds=0.0,
    )
    app.state.authz_service = AuthzService(app.state.authz_repository)
    app.state.conversation_repository = MemoryConversationRepository()
    app.state.message_repository = MemoryMessageRepository()
    app.state.usage_repository = MemoryUsageRepository()


def _chat_payload():
    return {
        "model": "fake-static",
        "messages": [
            {
                "role": "user",
                "parts": [{"type": "text", "text": "Hello"}],
            }
        ],
    }


def test_chat_runtime_unavailable_returns_500():
    app = _build_app()

    def _raise_runtime_error():
        raise RuntimeError("runtime not configured")

    app.dependency_overrides[get_run_service] = _raise_runtime_error
    with TestClient(app, raise_server_exceptions=False) as client:
        _initialize_state(app)
        response = client.post("/api/chat", json=_chat_payload())
        assert response.status_code == 500


def test_chat_stream_failure_returns_503():
    app = _build_app()

    def _raise_service_unavailable():
        raise HTTPException(status_code=503, detail="Upstream unavailable")

    app.dependency_overrides[get_run_service] = _raise_service_unavailable
    with TestClient(app, raise_server_exceptions=False) as client:
        _initialize_state(app)
        response = client.post("/api/chat", json=_chat_payload())
        assert response.status_code == 503
