from datetime import datetime, timezone

from app.features.conversations.models import ConversationMetadata, ConversationResponse
from app.features.conversations.ports import ConversationRepository
from app.features.messages.ports import MessageRepository


class ConversationService:
    def __init__(
        self,
        conversation_repo: ConversationRepository,
        message_repo: MessageRepository,
    ) -> None:
        self._conversation_repo = conversation_repo
        self._message_repo = message_repo

    async def list_conversations(
        self, tenant_id: str, user_id: str
    ) -> list[ConversationMetadata]:
        return await self._conversation_repo.list_conversations(tenant_id, user_id)

    async def list_archived_conversations(
        self, tenant_id: str, user_id: str
    ) -> list[ConversationMetadata]:
        return await self._conversation_repo.list_archived_conversations(tenant_id, user_id)

    async def get_conversation(
        self, tenant_id: str, user_id: str, conversation_id: str
    ) -> ConversationResponse | None:
        metadata = await self._conversation_repo.get_conversation(
            tenant_id, user_id, conversation_id
        )
        if metadata is None:
            return None
        messages = await self._message_repo.list_messages(tenant_id, conversation_id)
        return ConversationResponse(
            id=metadata.id,
            title=metadata.title,
            updatedAt=metadata.updatedAt,
            messages=messages,
        )

    async def archive_all_conversations(self, tenant_id: str, user_id: str) -> int:
        ids = await self._conversation_repo.list_all_conversation_ids(tenant_id, user_id)
        updated_at = None
        count = 0
        for conversation_id in ids:
            if not updated_at:
                updated_at = datetime.now(timezone.utc).isoformat()
            updated = await self._conversation_repo.archive_conversation(
                tenant_id,
                user_id,
                conversation_id,
                archived=True,
                updated_at=updated_at,
            )
            if updated:
                count += 1
        return count

    async def delete_all_conversations(self, tenant_id: str, user_id: str) -> int:
        ids = await self._conversation_repo.list_all_conversation_ids(tenant_id, user_id)
        count = 0
        for conversation_id in ids:
            deleted = await self._conversation_repo.delete_conversation(
                tenant_id, user_id, conversation_id
            )
            await self._message_repo.delete_messages(tenant_id, conversation_id)
            if deleted:
                count += 1
        return count
