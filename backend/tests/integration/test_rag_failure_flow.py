from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.core.application import create_app
from app.core.dependencies import get_chat_capabilities
from app.features.authz.service import AuthzService
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


def _build_app():
    return create_app()


def _initialize_state(app) -> None:
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


def _rag_payload():
    return {
        "query": "hello",
        "dataSource": "tool01",
        "provider": "memory",
        "model": "fake-static",
        "topK": 1,
    }


def test_rag_external_failure_returns_503():
    app = _build_app()

    def _raise_service_unavailable():
        raise HTTPException(status_code=503, detail="Retrieval service unavailable")

    app.dependency_overrides[get_chat_capabilities] = _raise_service_unavailable
    with TestClient(app, raise_server_exceptions=False) as client:
        _initialize_state(app)
        response = client.post("/api/rag/query", json=_rag_payload())
        assert response.status_code == 503


def test_rag_external_failure_returns_500():
    app = _build_app()

    def _raise_runtime_error():
        raise RuntimeError("retrieval backend failure")

    app.dependency_overrides[get_chat_capabilities] = _raise_runtime_error
    with TestClient(app, raise_server_exceptions=False) as client:
        _initialize_state(app)
        response = client.post("/api/rag/query", json=_rag_payload())
        assert response.status_code == 500
