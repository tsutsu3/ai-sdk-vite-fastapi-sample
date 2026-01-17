import logging

from app.features.conversations.models import ConversationRecord
from app.features.conversations.schemas import ConversationResponse
from app.features.conversations.tenant_scoped import TenantScopedConversationRepository
from app.features.messages.ports import MessageRepository


class ConversationService:
    """Service for conversation retrieval and bulk operations.

    This service centralizes conversation orchestration so API handlers do not
    need to know how repositories are composed. It coordinates metadata and
    message retrieval, and provides bulk operations with consistent behavior
    across storage backends.
    """

    def __init__(
        self,
        conversation_repo: TenantScopedConversationRepository,
        message_repo: MessageRepository,
    ) -> None:
        """Initialize the conversation service.

        Args:
            conversation_repo: Tenant-scoped conversation repository.
            message_repo: Message repository.
        """
        self._conversation_repo = conversation_repo
        self._message_repo = message_repo
        self._logger = logging.getLogger(__name__)

    async def list_conversations(
        self,
        user_id: str,
        limit: int | None = None,
        continuation_token: str | None = None,
    ) -> tuple[list[ConversationRecord], str | None]:
        """List active conversations for a user.

        This keeps the active list consistent with archived state rules across
        repository implementations.

        Args:
            user_id: User identifier.

        Returns:
            list[ConversationRecord]: Active conversations.
        """
        return await self._conversation_repo.list_conversations(
            user_id,
            limit=limit,
            continuation_token=continuation_token,
        )

    async def list_archived_conversations(
        self,
        user_id: str,
        limit: int | None = None,
        continuation_token: str | None = None,
    ) -> tuple[list[ConversationRecord], str | None]:
        """List archived conversations for a user.

        This isolates archive semantics from the API layer.

        Args:
            user_id: User identifier.

        Returns:
            list[ConversationRecord]: Archived conversations.
        """
        return await self._conversation_repo.list_archived_conversations(
            user_id,
            limit=limit,
            continuation_token=continuation_token,
        )

    async def get_conversation(
        self, user_id: str, conversation_id: str
    ) -> ConversationResponse | None:
        """Fetch a conversation with messages.

        This composes metadata and message retrieval into a single response
        used by the chat UI.

        Args:
            user_id: User identifier.
            conversation_id: Conversation identifier.

        Returns:
            ConversationResponse | None: Conversation or None if missing.
        """
        metadata = await self._conversation_repo.get_conversation(user_id, conversation_id)
        if metadata is None:
            self._logger.info(
                "conversations.detail.miss tenant_id=%s user_id=%s conversation_id=%s",
                self._conversation_repo.tenant_id,
                user_id,
                conversation_id,
            )
            return None
        self._logger.info(
            "conversations.detail.loaded tenant_id=%s user_id=%s conversation_id=%s",
            self._conversation_repo.tenant_id,
            user_id,
            conversation_id,
        )
        messages, _ = await self._message_repo.list_messages(
            self._conversation_repo.tenant_id,
            user_id,
            conversation_id,
        )
        return ConversationResponse(
            id=metadata.id,
            title=metadata.title,
            toolId=metadata.toolId,
            archived=metadata.archived,
            updatedAt=metadata.updatedAt,
            messages=messages,
        )

    async def archive_all_conversations(
        self, user_id: str, archived: bool = True
    ) -> list[ConversationRecord]:
        """Bulk update archive status for all conversations.

        This is used for settings actions like archive-all and ensures a
        consistent updatedAt timestamp for the batch.

        Args:
            user_id: User identifier.
            archived: Target archive state.

        Returns:
            list[ConversationRecord]: Updated conversation metadata.
        """
        ids = await self._conversation_repo.list_all_conversation_ids(user_id)
        self._logger.info(
            "conversations.archive_all.start tenant_id=%s user_id=%s count=%d archived=%s",
            self._conversation_repo.tenant_id,
            user_id,
            len(ids),
            archived,
        )
        updated_items: list[ConversationRecord] = []
        for conversation_id in ids:
            updated = await self._conversation_repo.archive_conversation(
                user_id,
                conversation_id,
                archived=archived,
            )
            if updated:
                updated_items.append(updated)
        self._logger.info(
            "conversations.archive_all.complete tenant_id=%s user_id=%s updated=%d archived=%s",
            self._conversation_repo.tenant_id,
            user_id,
            len(updated_items),
            archived,
        )
        return updated_items

    async def delete_all_conversations(self, user_id: str) -> int:
        """Delete all conversations and their messages.

        This is used for data-reset flows and performs best-effort cleanup.

        Args:
            user_id: User identifier.

        Returns:
            int: Count of deleted conversations.
        """
        ids = await self._conversation_repo.list_all_conversation_ids(user_id)
        self._logger.info(
            "conversations.delete_all.start tenant_id=%s user_id=%s count=%d",
            self._conversation_repo.tenant_id,
            user_id,
            len(ids),
        )
        count = 0
        for conversation_id in ids:
            deleted = await self._conversation_repo.delete_conversation(user_id, conversation_id)
            await self._message_repo.delete_messages(
                self._conversation_repo.tenant_id,
                user_id,
                conversation_id,
            )
            if deleted:
                count += 1
        self._logger.info(
            "conversations.delete_all.complete tenant_id=%s user_id=%s deleted=%d",
            self._conversation_repo.tenant_id,
            user_id,
            count,
        )
        return count
