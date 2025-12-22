from datetime import datetime, timezone

from app.features.conversations.models import ConversationMetadata
from app.features.conversations.ports import ConversationRepository
from app.shared.constants import DEFAULT_CHAT_TITLE


def current_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


class MemoryConversationRepository(ConversationRepository):
    def __init__(self) -> None:
        now = current_timestamp()
        self._conversation_store: dict[str, ConversationMetadata] = {
            "conv-quickstart": ConversationMetadata(
                id="conv-quickstart",
                title="Project kickoff chat",
                archived=False,
                updatedAt=now,
                createdAt=now,
            ),
            "conv-rag": ConversationMetadata(
                id="conv-rag",
                title="RAG tuning ideas",
                archived=False,
                updatedAt=now,
                createdAt=now,
            ),
        }

    async def list_conversations(
        self,
        tenant_id: str,
        user_id: str,
    ) -> list[ConversationMetadata]:
        return [
            ConversationMetadata(
                id=conv.id,
                title=conv.title or DEFAULT_CHAT_TITLE,
                updatedAt=conv.updatedAt or current_timestamp(),
                createdAt=conv.createdAt,
            )
            for conv in self._conversation_store.values()
            if not conv.archived
        ]

    async def list_archived_conversations(
        self,
        tenant_id: str,
        user_id: str,
    ) -> list[ConversationMetadata]:
        return [
            ConversationMetadata(
                id=conv.id,
                title=conv.title or DEFAULT_CHAT_TITLE,
                updatedAt=conv.updatedAt or current_timestamp(),
                createdAt=conv.createdAt,
            )
            for conv in self._conversation_store.values()
            if conv.archived
        ]

    async def get_conversation(
        self,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
    ) -> ConversationMetadata | None:
        conversation = self._conversation_store.get(conversation_id)
        if not conversation:
            return None
        return ConversationMetadata(
            id=conversation.id,
            title=conversation.title or DEFAULT_CHAT_TITLE,
            updatedAt=conversation.updatedAt or current_timestamp(),
            createdAt=conversation.createdAt,
        )

    async def upsert_conversation(
        self,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
        title: str,
        updated_at: str,
    ) -> ConversationMetadata:
        conversation = self._conversation_store.get(conversation_id)
        if conversation is None:
            conversation = ConversationMetadata(
                id=conversation_id,
                title=title or DEFAULT_CHAT_TITLE,
                archived=False,
                updatedAt=updated_at,
                createdAt=updated_at,
            )
        else:
            conversation = conversation.model_copy(
                update={
                    "title": title or DEFAULT_CHAT_TITLE,
                    "updatedAt": updated_at,
                }
            )
        self._conversation_store[conversation_id] = conversation

        return conversation

    async def archive_conversation(
        self,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
        archived: bool,
        updated_at: str,
    ) -> ConversationMetadata | None:
        conversation = self._conversation_store.get(conversation_id)
        if not conversation:
            return None
        updated = conversation.model_copy(
            update={
                "archived": archived,
                "updatedAt": updated_at,
            }
        )
        self._conversation_store[conversation_id] = updated
        return updated

    async def delete_conversation(
        self,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
    ) -> bool:
        return self._conversation_store.pop(conversation_id, None) is not None

    async def update_title(
        self,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
        title: str,
        updated_at: str,
    ) -> ConversationMetadata | None:
        conversation = self._conversation_store.get(conversation_id)
        if not conversation:
            return None
        updated = conversation.model_copy(
            update={
                "title": title or DEFAULT_CHAT_TITLE,
                "updatedAt": updated_at,
            }
        )
        self._conversation_store[conversation_id] = updated
        return updated

    async def list_all_conversation_ids(
        self,
        tenant_id: str,
        user_id: str,
    ) -> list[str]:
        return list(self._conversation_store.keys())
