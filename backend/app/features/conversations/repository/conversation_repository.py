from typing import Protocol

from app.features.conversations.models import (
    ConversationMetadata,
    ConversationResponse,
)


class ConversationRepository(Protocol):
    def list_conversations(self) -> list[ConversationMetadata]:
        """Return metadata for all conversations."""
        raise NotImplementedError

    def get_conversation(self, conversation_id: str) -> ConversationResponse | None:
        """Return a conversation by id."""
        raise NotImplementedError
