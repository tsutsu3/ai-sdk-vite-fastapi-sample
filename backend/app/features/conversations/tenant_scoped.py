from app.features.conversations.models import ConversationRecord
from app.features.conversations.ports import ConversationRepository


class TenantScopedConversationRepository:
    """Tenant-scoped wrapper for conversation repositories."""

    def __init__(self, tenant_id: str, repo: ConversationRepository) -> None:
        """Initialize the scoped repository.

        Args:
            tenant_id: Tenant identifier.
            repo: Conversation repository.
        """
        self._tenant_id = tenant_id
        self._repo = repo

    @property
    def tenant_id(self) -> str:
        """Return the tenant identifier."""
        return self._tenant_id

    async def list_conversations(
        self,
        user_id: str,
        limit: int | None = None,
        continuation_token: str | None = None,
    ) -> tuple[list[ConversationRecord], str | None]:
        """List active conversations for a user.

        Args:
            user_id: User identifier.

        Returns:
            list[ConversationRecord]: Active conversations.
        """
        return await self._repo.list_conversations(
            self._tenant_id,
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

        Args:
            user_id: User identifier.

        Returns:
            list[ConversationRecord]: Archived conversations.
        """
        return await self._repo.list_archived_conversations(
            self._tenant_id,
            user_id,
            limit=limit,
            continuation_token=continuation_token,
        )

    async def get_conversation(
        self,
        user_id: str,
        conversation_id: str,
    ) -> ConversationRecord | None:
        """Fetch conversation metadata by id.

        Args:
            user_id: User identifier.
            conversation_id: Conversation identifier.

        Returns:
            ConversationRecord | None: Conversation metadata or None.
        """
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
    ) -> ConversationRecord:
        """Create or update conversation metadata.

        Args:
            user_id: User identifier.
            conversation_id: Conversation identifier.
            title: Conversation title.
        Returns:
            ConversationRecord: Updated metadata.
        """
        return await self._repo.upsert_conversation(
            self._tenant_id,
            user_id,
            conversation_id,
            title,
        )

    async def archive_conversation(
        self,
        user_id: str,
        conversation_id: str,
        archived: bool,
    ) -> ConversationRecord | None:
        """Archive or unarchive a conversation.

        Args:
            user_id: User identifier.
            conversation_id: Conversation identifier.
            archived: Target archive state.
        Returns:
            ConversationRecord | None: Updated metadata or None.
        """
        return await self._repo.archive_conversation(
            self._tenant_id,
            user_id,
            conversation_id,
            archived,
        )

    async def delete_conversation(
        self,
        user_id: str,
        conversation_id: str,
    ) -> bool:
        """Delete a conversation.

        Args:
            user_id: User identifier.
            conversation_id: Conversation identifier.

        Returns:
            bool: True if deleted, False otherwise.
        """
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
    ) -> ConversationRecord | None:
        """Update a conversation title.

        Args:
            user_id: User identifier.
            conversation_id: Conversation identifier.
            title: New title.
        Returns:
            ConversationRecord | None: Updated metadata or None.
        """
        return await self._repo.update_title(
            self._tenant_id,
            user_id,
            conversation_id,
            title,
        )

    async def list_all_conversation_ids(self, user_id: str) -> list[str]:
        """List all conversation ids for a user.

        Args:
            user_id: User identifier.

        Returns:
            list[str]: Conversation identifiers.
        """
        return await self._repo.list_all_conversation_ids(self._tenant_id, user_id)
