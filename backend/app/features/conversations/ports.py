from typing import Protocol

from app.features.conversations.models import (
    ConversationRecord,
)


class ConversationRepository(Protocol):
    """Interface for conversation persistence.

    This abstraction exists to decouple the API and service layer from storage
    details so the same behaviors work across memory, local, and Cosmos backends.
    Implementations store and query conversation metadata while preserving tenant
    and user scoping.
    """

    async def list_conversations(
        self,
        tenant_id: str,
        user_id: str,
        limit: int | None = None,
        continuation_token: str | None = None,
    ) -> tuple[list[ConversationRecord], str | None]:
        """List active conversations for a user.

        Archived conversations are excluded.

        Args:
            tenant_id: Tenant identifier.
            user_id: User identifier.
            limit: Optional maximum number of conversations to return.
            continuation_token: Continuation token for paging.

        Returns:
            tuple[list[ConversationRecord], str | None]: Conversations and next token.
        """
        raise NotImplementedError

    async def list_archived_conversations(
        self,
        tenant_id: str,
        user_id: str,
        limit: int | None = None,
        continuation_token: str | None = None,
    ) -> tuple[list[ConversationRecord], str | None]:
        """List archived conversations for a user.

        Active conversations are excluded.

        Args:
            tenant_id: Tenant identifier.
            user_id: User identifier.
            limit: Optional maximum number of conversations to return.
            continuation_token: Continuation token for paging.

        Returns:
            tuple[list[ConversationRecord], str | None]: Conversations and next token.
        """
        raise NotImplementedError

    async def get_conversation(
        self,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
    ) -> ConversationRecord | None:
        """Fetch conversation metadata by id.

        Returns None when the conversation does not exist.

        Args:
            tenant_id: Tenant identifier.
            user_id: User identifier.
            conversation_id: Conversation identifier.

        Returns:
            ConversationRecord | None: Conversation metadata or None.
        """
        raise NotImplementedError

    async def upsert_conversation(
        self,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
        title: str,
        tool_id: str | None = None,
    ) -> ConversationRecord:
        """Create or update conversation metadata.

        Args:
            tenant_id: Tenant identifier.
            user_id: User identifier.
            conversation_id: Conversation identifier.
            title: Conversation title.
        Returns:
            ConversationRecord: Updated conversation metadata.
        """
        raise NotImplementedError

    async def archive_conversation(
        self,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
        archived: bool,
    ) -> ConversationRecord | None:
        """Archive or unarchive a conversation.

        Returns None when the conversation does not exist.

        Args:
            tenant_id: Tenant identifier.
            user_id: User identifier.
            conversation_id: Conversation identifier.
            archived: Target archived state.
        Returns:
            ConversationRecord | None: Updated metadata or None.
        """
        raise NotImplementedError

    async def delete_conversation(
        self,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
    ) -> bool:
        """Delete a conversation.

        Returns True on deletion and False if missing.

        Args:
            tenant_id: Tenant identifier.
            user_id: User identifier.
            conversation_id: Conversation identifier.

        Returns:
            bool: True if deleted, False if missing.
        """
        raise NotImplementedError

    async def update_title(
        self,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
        title: str,
    ) -> ConversationRecord | None:
        """Update a conversation title.

        Returns None when the conversation does not exist.

        Args:
            tenant_id: Tenant identifier.
            user_id: User identifier.
            conversation_id: Conversation identifier.
            title: New title.
        Returns:
            ConversationRecord | None: Updated metadata or None.
        """
        raise NotImplementedError

    async def list_all_conversation_ids(
        self,
        tenant_id: str,
        user_id: str,
    ) -> list[str]:
        """List conversation ids including archived ones.

        Used for bulk operations and cleanup.

        Args:
            tenant_id: Tenant identifier.
            user_id: User identifier.

        Returns:
            list[str]: Conversation identifiers.
        """
        raise NotImplementedError
