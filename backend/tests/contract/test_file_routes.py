from fastapi.testclient import TestClient

from app.core.application import create_app
from app.core.config import Settings
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
from app.infra.storage.memory_blob_storage import MemoryBlobStorage


def _create_client() -> TestClient:
    app = create_app()
    app.state.app_config = Settings().to_app_config()
    client = TestClient(app)
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
    app.state.blob_storage = MemoryBlobStorage()
    return client


def test_file_upload_response_shape(client):
    response = client.post(
        "/api/file",
        files={"file": ("hello.txt", b"Hello", "text/plain")},
    )
    assert response.status_code == 201
    payload = response.json()
    assert "fileId" in payload
    assert payload.get("contentType") == "text/plain"
    assert payload.get("size") == 5


def test_file_download_response_shape(client):
    upload = client.post(
        "/api/file",
        files={"file": ("hello.txt", b"Hello", "text/plain")},
    )
    assert upload.status_code == 201
    file_id = upload.json().get("fileId")
    assert file_id

    response = client.get(f"/api/file/{file_id}/download")
    assert response.status_code == 200
    assert response.content == b"Hello"


def test_file_download_not_found(client):
    response = client.get("/api/file/file-not-found/download")
    assert response.status_code == 404


def test_file_upload_rejects_unsupported_type(monkeypatch):
    monkeypatch.setenv("FILE_UPLOAD_ALLOWED_TYPES", "image/png")
    client = _create_client()
    try:
        response = client.post(
            "/api/file",
            files={"file": ("hello.txt", b"Hello", "text/plain")},
        )
        assert response.status_code == 415
    finally:
        client.close()


def test_file_upload_rejects_too_large(monkeypatch):
    monkeypatch.setenv("FILE_UPLOAD_MAX_BYTES", "4")
    client = _create_client()
    try:
        response = client.post(
            "/api/file",
            files={"file": ("hello.txt", b"Hello", "text/plain")},
        )
        assert response.status_code == 413
    finally:
        client.close()
