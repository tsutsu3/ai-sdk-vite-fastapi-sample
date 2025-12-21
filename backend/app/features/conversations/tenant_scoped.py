from app.features.conversations.models import ConversationMetadata
from app.features.conversations.ports import ConversationRepository


class TenantScopedConversationRepository:
    def __init__(self, tenant_id: str, repo: ConversationRepository) -> None:
        self._tenant_id = tenant_id
        self._repo = repo

    @property
    def tenant_id(self) -> str:
        return self._tenant_id

    async def list_conversations(self, user_id: str) -> list[ConversationMetadata]:
        return await self._repo.list_conversations(self._tenant_id, user_id)

    async def list_archived_conversations(self, user_id: str) -> list[ConversationMetadata]:
        return await self._repo.list_archived_conversations(self._tenant_id, user_id)

    async def get_conversation(
        self,
        user_id: str,
        conversation_id: str,
    ) -> ConversationMetadata | None:
        return await self._repo.get_conversation(
            self._tenant_id,
            user_id,
            conversation_id,
        )

    async def upsert_conversation(
        self,
        user_id: str,
        conversation_id: str,
        title: str,
        updated_at: str,
    ) -> ConversationMetadata:
        return await self._repo.upsert_conversation(
            self._tenant_id,
            user_id,
            conversation_id,
            title,
            updated_at,
        )

    async def archive_conversation(
        self,
        user_id: str,
        conversation_id: str,
        archived: bool,
        updated_at: str,
    ) -> ConversationMetadata | None:
        return await self._repo.archive_conversation(
            self._tenant_id,
            user_id,
            conversation_id,
            archived,
            updated_at,
        )

    async def delete_conversation(
        self,
        user_id: str,
        conversation_id: str,
    ) -> bool:
        return await self._repo.delete_conversation(
            self._tenant_id,
            user_id,
            conversation_id,
        )

    async def update_title(
        self,
        user_id: str,
        conversation_id: str,
        title: str,
        updated_at: str,
    ) -> ConversationMetadata | None:
        return await self._repo.update_title(
            self._tenant_id,
            user_id,
            conversation_id,
            title,
            updated_at,
        )

    async def list_all_conversation_ids(self, user_id: str) -> list[str]:
        return await self._repo.list_all_conversation_ids(self._tenant_id, user_id)
