from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.core.application import create_app
from app.features.authz.service import AuthzService
from app.features.conversations.models import ConversationRecord
from app.features.conversations.ports import ConversationRepository
from app.infra.repository.memory.memory_authz_repository import MemoryAuthzRepository
from app.infra.repository.memory.memory_messages_repository import (
    MemoryMessageRepository,
)


class CapturingConversationRepository(ConversationRepository):
    def __init__(self) -> None:
        self.seen_tenant_ids: list[str] = []

    async def list_conversations(self, tenant_id: str, user_id: str):
        self.seen_tenant_ids.append(tenant_id)
        return [
            ConversationRecord(
                id="conv-tenant",
                title="Tenant scoped",
                archived=False,
                updatedAt=datetime(2024, 1, 1, tzinfo=timezone.utc),
                createdAt=datetime(2024, 1, 1, tzinfo=timezone.utc),
            )
        ]

    async def list_archived_conversations(self, tenant_id: str, user_id: str):
        return []

    async def get_conversation(self, tenant_id: str, user_id: str, conversation_id: str):
        return None

    async def upsert_conversation(
        self,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
        title: str,
    ):
        updated_at = datetime.now(timezone.utc)
        return ConversationRecord(
            id=conversation_id,
            title=title,
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


def test_conversation_routes_pass_tenant_id():
    app = create_app()
    repo = CapturingConversationRepository()
    with TestClient(app) as client:
        app.state.authz_repository = MemoryAuthzRepository()
        app.state.authz_service = AuthzService(app.state.authz_repository)
        app.state.conversation_repository = repo
        app.state.message_repository = MemoryMessageRepository()
        response = client.get("/api/conversations")
        assert response.status_code == 200
        assert repo.seen_tenant_ids
        assert repo.seen_tenant_ids[0] == "tenant-demo"
