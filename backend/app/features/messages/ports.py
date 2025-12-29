from typing import Protocol

from app.features.messages.models import MessageRecord


class MessageRepository(Protocol):
    """Interface for message persistence.

    This abstraction keeps message storage independent of API and service logic,
    enabling backends like memory, local files, or Cosmos DB to be swapped
    without changing call sites.
    """

    async def list_messages(
        self,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
        limit: int | None = None,
        continuation_token: str | None = None,
        descending: bool = False,
    ) -> tuple[list[MessageRecord], str | None]:
        """List messages for a conversation.

        Returns messages in chat-compatible format.

        Args:
            tenant_id: Tenant identifier.
            user_id: User identifier.
            conversation_id: Conversation identifier.
            limit: Optional maximum number of messages to return.
            continuation_token: Continuation token for paging.
            descending: When true, newest messages are returned first.

        Returns:
            tuple[list[MessageRecord], str | None]: Messages and next continuation token.
        """
        raise NotImplementedError

    async def upsert_messages(
        self,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
        messages: list[MessageRecord],
    ) -> list[MessageRecord]:
        """Create or update messages for a conversation.

        The provided list is merged by message id (existing messages are updated,
        new messages are appended).

        Args:
            tenant_id: Tenant identifier.
            user_id: User identifier.
            conversation_id: Conversation identifier.
            messages: Messages to persist.
        Returns:
            list[MessageRecord]: Updated message records.
        """
        raise NotImplementedError

    async def delete_messages(self, tenant_id: str, user_id: str, conversation_id: str) -> None:
        """Delete all messages for a conversation.

        This removes only messages, not the conversation metadata.

        Args:
            tenant_id: Tenant identifier.
            user_id: User identifier.
            conversation_id: Conversation identifier.
        """
        raise NotImplementedError

    async def update_message_reaction(
        self,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
        message_id: str,
        reaction: str | None,
    ) -> MessageRecord | None:
        """Update reaction metadata for a message.

        Args:
            tenant_id: Tenant identifier.
            user_id: User identifier.
            conversation_id: Conversation identifier.
            message_id: Message identifier.
            reaction: "like", "dislike", or None to clear.

        Returns:
            MessageRecord | None: Updated message or None if missing.
        """
        raise NotImplementedError
