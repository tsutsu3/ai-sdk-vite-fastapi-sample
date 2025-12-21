from datetime import datetime, timezone

from app.features.conversations.models import ConversationMetadata
from app.features.conversations.ports import ConversationRepository
from app.shared.constants import DEFAULT_CHAT_TITLE


def current_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


class MemoryConversationRepository(ConversationRepository):
    def __init__(self) -> None:
        self._conversation_store = {
            "conv-quickstart": {
                "id": "conv-quickstart",
                "title": "Project kickoff chat",
                "updatedAt": current_timestamp(),
                "createdAt": current_timestamp(),
                "archived": False,
            },
            "conv-rag": {
                "id": "conv-rag",
                "title": "RAG tuning ideas",
                "updatedAt": current_timestamp(),
                "createdAt": current_timestamp(),
                "archived": False,
            },
        }

    async def list_conversations(
        self,
        tenant_id: str,
        user_id: str,
    ) -> list[ConversationMetadata]:
        return [
            ConversationMetadata(
                id=conv["id"],
                title=conv.get("title") or DEFAULT_CHAT_TITLE,
                updatedAt=conv.get("updatedAt") or current_timestamp(),
                createdAt=conv.get("createdAt"),
            )
            for conv in self._conversation_store.values()
            if not conv.get("archived", False)
        ]

    async def list_archived_conversations(
        self,
        tenant_id: str,
        user_id: str,
    ) -> list[ConversationMetadata]:
        return [
            ConversationMetadata(
                id=conv["id"],
                title=conv.get("title") or DEFAULT_CHAT_TITLE,
                updatedAt=conv.get("updatedAt") or current_timestamp(),
                createdAt=conv.get("createdAt"),
            )
            for conv in self._conversation_store.values()
            if conv.get("archived", False)
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
            id=conversation["id"],
            title=conversation.get("title") or DEFAULT_CHAT_TITLE,
            updatedAt=conversation.get("updatedAt") or current_timestamp(),
            createdAt=conversation.get("createdAt"),
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
            conversation = {
                "id": conversation_id,
                "title": title or DEFAULT_CHAT_TITLE,
                "updatedAt": updated_at,
                "createdAt": updated_at,
            }
            self._conversation_store[conversation_id] = conversation
        else:
            conversation["updatedAt"] = updated_at
            conversation["title"] = title
            conversation.setdefault("archived", False)

        return ConversationMetadata(
            id=conversation["id"],
            title=conversation.get("title") or DEFAULT_CHAT_TITLE,
            updatedAt=conversation.get("updatedAt") or current_timestamp(),
            createdAt=conversation.get("createdAt"),
        )

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
        conversation["archived"] = archived
        conversation["updatedAt"] = updated_at
        return ConversationMetadata(
            id=conversation["id"],
            title=conversation.get("title") or DEFAULT_CHAT_TITLE,
            updatedAt=conversation.get("updatedAt") or current_timestamp(),
            createdAt=conversation.get("createdAt"),
        )

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
        conversation["title"] = title
        conversation["updatedAt"] = updated_at
        return ConversationMetadata(
            id=conversation["id"],
            title=conversation.get("title") or DEFAULT_CHAT_TITLE,
            updatedAt=conversation.get("updatedAt") or current_timestamp(),
            createdAt=conversation.get("createdAt"),
        )

    async def list_all_conversation_ids(
        self,
        tenant_id: str,
        user_id: str,
    ) -> list[str]:
        return list(self._conversation_store.keys())
