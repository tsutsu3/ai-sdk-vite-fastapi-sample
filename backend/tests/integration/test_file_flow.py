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
from app.shared.ports import UploadedFileObject


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


def test_file_upload_and_download(client):
    upload = client.post(
        "/api/file",
        files={"file": ("hello.txt", b"Hello", "text/plain")},
    )
    assert upload.status_code == 201
    payload = upload.json()
    file_id = payload.get("fileId")
    assert file_id
    assert payload.get("contentType") == "text/plain"
    assert payload.get("size") == 5

    download = client.get(f"/api/file/{file_id}/download")
    assert download.status_code == 200
    assert download.content == b"Hello"


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


class FailingBlobStorage:
    async def upload(self, data: bytes, content_type: str, filename: str) -> UploadedFileObject:
        raise RuntimeError("storage unavailable")

    async def download(self, file_id: str) -> bytes | None:
        raise RuntimeError("storage unavailable")

    async def get_object_url(
        self, file_id: str, expires_in_seconds: int | None = None
    ) -> str | None:
        return None


def test_file_upload_storage_failure_returns_500():
    app = create_app()
    with TestClient(app, raise_server_exceptions=False) as client:
        app.state.blob_storage = FailingBlobStorage()
        response = client.post(
            "/api/file",
            files={"file": ("hello.txt", b"Hello", "text/plain")},
        )
        assert response.status_code == 500
