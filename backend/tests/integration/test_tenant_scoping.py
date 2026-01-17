from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.core.application import create_app
from app.features.authz.service import AuthzService
from app.features.conversations.models import ConversationRecord
from app.features.conversations.ports import ConversationRepository
from app.infra.fixtures.authz.local_data import (
    PROVISIONING,
    TENANTS,
    USER_IDENTITIES,
    USERS,
)
from app.infra.repository.memory.memory_authz_repository import MemoryAuthzRepository
from app.infra.repository.memory.memory_messages_repository import (
    MemoryMessageRepository,
)


class CapturingConversationRepository(ConversationRepository):
    def __init__(self) -> None:
        self.seen_tenant_ids: list[str] = []

    async def list_conversations(
        self,
        tenant_id: str,
        user_id: str,
        limit: int | None = None,
        continuation_token: str | None = None,
    ):
        self.seen_tenant_ids.append(tenant_id)
        return (
            [
                ConversationRecord(
                    id="conv-tenant",
                    title="Tenant scoped",
                    archived=False,
                    updatedAt=datetime(2024, 1, 1, tzinfo=timezone.utc),
                    createdAt=datetime(2024, 1, 1, tzinfo=timezone.utc),
                )
            ],
            None,
        )

    async def list_archived_conversations(
        self,
        tenant_id: str,
        user_id: str,
        limit: int | None = None,
        continuation_token: str | None = None,
    ):
        return ([], None)

    async def get_conversation(self, tenant_id: str, user_id: str, conversation_id: str):
        return None

    async def upsert_conversation(
        self,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
        title: str,
        tool_id: str | None = None,
    ):
        updated_at = datetime.now(timezone.utc)
        return ConversationRecord(
            id=conversation_id,
            title=title,
            toolId=tool_id,
            archived=False,
            updatedAt=updated_at,
            createdAt=updated_at,
        )

    async def archive_conversation(
        self,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
        archived: bool,
    ):
        return None

    async def delete_conversation(self, tenant_id: str, user_id: str, conversation_id: str):
        return False

    async def update_title(
        self,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
        title: str,
    ):
        return None

    async def list_all_conversation_ids(self, tenant_id: str, user_id: str):
        return []


def test_conversation_routes_pass_tenant_id(monkeypatch):
    monkeypatch.setenv("AUTH_PROVIDER", "local")
    monkeypatch.setenv("LOCAL_AUTH_USER_EMAIL", "local.user001@example.com")
    monkeypatch.setenv("CHAT_DEFAULT_MODEL", "fake-static")
    monkeypatch.setenv("CHAT_TITLE_MODEL", "fake-static")
    app = create_app()
    repo = CapturingConversationRepository()
    with TestClient(app) as client:
        app.state.authz_repository = MemoryAuthzRepository(
            tenants=TENANTS,
            users=USERS,
            user_identities=USER_IDENTITIES,
            provisioning=PROVISIONING,
        )
        app.state.authz_service = AuthzService(app.state.authz_repository)
        app.state.conversation_repository = repo
        app.state.message_repository = MemoryMessageRepository()
        response = client.get("/api/conversations")
        assert response.status_code == 200
        assert repo.seen_tenant_ids
        assert repo.seen_tenant_ids[0] == "id-tenant001"
