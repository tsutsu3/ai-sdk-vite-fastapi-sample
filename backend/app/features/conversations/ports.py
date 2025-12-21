from typing import Protocol

from app.features.conversations.models import (
    ConversationMetadata,
    ConversationResponse,
)


class ConversationRepository(Protocol):
    async def list_conversations(
        self,
        tenant_id: str,
        user_id: str,
    ) -> list[ConversationMetadata]:
        """Return metadata for all conversations."""
        raise NotImplementedError

    async def list_archived_conversations(
        self,
        tenant_id: str,
        user_id: str,
    ) -> list[ConversationMetadata]:
        """Return metadata for archived conversations."""
        raise NotImplementedError

    async def get_conversation(
        self,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
    ) -> ConversationMetadata | None:
        """Return conversation metadata by id."""
        raise NotImplementedError

    async def upsert_conversation(
        self,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
        title: str,
        updated_at: str,
    ) -> ConversationMetadata:
        """Create or update conversation metadata."""
        raise NotImplementedError

    async def archive_conversation(
        self,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
        archived: bool,
        updated_at: str,
    ) -> ConversationMetadata | None:
        """Archive or unarchive a conversation."""
        raise NotImplementedError

    async def delete_conversation(
        self,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
    ) -> bool:
        """Delete a conversation."""
        raise NotImplementedError

    async def update_title(
        self,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
        title: str,
        updated_at: str,
    ) -> ConversationMetadata | None:
        """Update a conversation title."""
        raise NotImplementedError

    async def list_all_conversation_ids(
        self,
        tenant_id: str,
        user_id: str,
    ) -> list[str]:
        """Return ids for all conversations including archived ones."""
        raise NotImplementedError
