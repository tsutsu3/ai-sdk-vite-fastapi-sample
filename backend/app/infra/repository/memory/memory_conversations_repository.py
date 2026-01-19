from app.features.conversations.models import ConversationRecord
from app.features.conversations.ports import ConversationRepository
from app.shared.constants import DEFAULT_CHAT_TITLE
from app.shared.time import now_datetime


class MemoryConversationRepository(ConversationRepository):
    def __init__(self) -> None:
        now = now_datetime()
        default_conversations = {
            "conv-quickstart": ConversationRecord(
                id="conv-quickstart",
                title="Project kickoff chat",
                toolId="chat",
                archived=False,
                updatedAt=now,
                createdAt=now,
            ),
            "conv-rag": ConversationRecord(
                id="conv-rag",
                title="RAG tuning ideas",
                toolId="rag01",
                archived=False,
                updatedAt=now,
                createdAt=now,
            ),
        }
        self._conversation_store: dict[tuple[str, str], dict[str, ConversationRecord]] = {
            ("id-tenant001", "local-user-001"): dict(default_conversations),
            ("id-tenant001", "local-user-001-01"): dict(default_conversations),
        }

    def _get_store(self, tenant_id: str, user_id: str) -> dict[str, ConversationRecord]:
        return self._conversation_store.get((tenant_id, user_id), {})

    def _set_store(
        self,
        tenant_id: str,
        user_id: str,
        store: dict[str, ConversationRecord],
    ) -> None:
        self._conversation_store[(tenant_id, user_id)] = store

    async def list_conversations(
        self,
        tenant_id: str,
        user_id: str,
        limit: int | None = None,
        continuation_token: str | None = None,
    ) -> tuple[list[ConversationRecord], str | None]:
        store = self._get_store(tenant_id, user_id)
        conversations = [
            ConversationRecord(
                id=conv.id,
                title=conv.title or DEFAULT_CHAT_TITLE,
                toolId=conv.toolId,
                archived=False,
                updatedAt=conv.updatedAt or now_datetime(),
                createdAt=conv.createdAt,
            )
            for conv in store.values()
            if not conv.archived
        ]
        conversations.sort(key=lambda item: item.updatedAt, reverse=True)
        if limit is None:
            return (conversations, None)
        safe_limit = max(limit, 0)
        safe_offset = 0
        if continuation_token:
            try:
                safe_offset = max(int(continuation_token), 0)
            except ValueError:
                safe_offset = 0
        sliced = conversations[safe_offset : safe_offset + safe_limit]
        next_offset = safe_offset + len(sliced)
        next_token = str(next_offset) if next_offset < len(conversations) else None
        return (sliced, next_token)

    async def list_archived_conversations(
        self,
        tenant_id: str,
        user_id: str,
        limit: int | None = None,
        continuation_token: str | None = None,
    ) -> tuple[list[ConversationRecord], str | None]:
        store = self._get_store(tenant_id, user_id)
        conversations = [
            ConversationRecord(
                id=conv.id,
                title=conv.title or DEFAULT_CHAT_TITLE,
                toolId=conv.toolId,
                archived=True,
                updatedAt=conv.updatedAt or now_datetime(),
                createdAt=conv.createdAt,
            )
            for conv in store.values()
            if conv.archived
        ]
        conversations.sort(key=lambda item: item.updatedAt, reverse=True)
        if limit is None:
            return (conversations, None)
        safe_limit = max(limit, 0)
        safe_offset = 0
        if continuation_token:
            try:
                safe_offset = max(int(continuation_token), 0)
            except ValueError:
                safe_offset = 0
        sliced = conversations[safe_offset : safe_offset + safe_limit]
        next_offset = safe_offset + len(sliced)
        next_token = str(next_offset) if next_offset < len(conversations) else None
        return (sliced, next_token)

    async def get_conversation(
        self,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
    ) -> ConversationRecord | None:
        conversation = self._get_store(tenant_id, user_id).get(conversation_id)
        if not conversation:
            return None
        return ConversationRecord(
            id=conversation.id,
            title=conversation.title or DEFAULT_CHAT_TITLE,
            toolId=conversation.toolId,
            updatedAt=conversation.updatedAt or now_datetime(),
            createdAt=conversation.createdAt,
        )

    async def upsert_conversation(
        self,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
        title: str,
        tool_id: str | None = None,
    ) -> ConversationRecord:
        updated_at = now_datetime()
        store = dict(self._get_store(tenant_id, user_id))
        conversation = store.get(conversation_id)
        if conversation is None:
            conversation = ConversationRecord(
                id=conversation_id,
                title=title or DEFAULT_CHAT_TITLE,
                toolId=tool_id or "chat",
                archived=False,
                updatedAt=updated_at,
                createdAt=updated_at,
            )
        else:
            conversation = conversation.model_copy(
                update={
                    "title": title or DEFAULT_CHAT_TITLE,
                    "toolId": tool_id or conversation.toolId,
                    "updatedAt": updated_at,
                }
            )
        store[conversation_id] = conversation
        self._set_store(tenant_id, user_id, store)

        return conversation

    async def archive_conversation(
        self,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
        archived: bool,
    ) -> ConversationRecord | None:
        store = dict(self._get_store(tenant_id, user_id))
        conversation = store.get(conversation_id)
        if not conversation:
            return None
        updated_at = now_datetime()
        updated = conversation.model_copy(
            update={
                "archived": archived,
                "updatedAt": updated_at,
            }
        )
        store[conversation_id] = updated
        self._set_store(tenant_id, user_id, store)
        return updated

    async def delete_conversation(
        self,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
    ) -> bool:
        store = dict(self._get_store(tenant_id, user_id))
        deleted = store.pop(conversation_id, None) is not None
        if deleted:
            self._set_store(tenant_id, user_id, store)
        return deleted

    async def update_title(
        self,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
        title: str,
    ) -> ConversationRecord | None:
        store = dict(self._get_store(tenant_id, user_id))
        conversation = store.get(conversation_id)
        if not conversation:
            return None
        updated_at = now_datetime()
        updated = conversation.model_copy(
            update={
                "title": title or DEFAULT_CHAT_TITLE,
                "updatedAt": updated_at,
            }
        )
        store[conversation_id] = updated
        self._set_store(tenant_id, user_id, store)
        return updated

    async def list_all_conversation_ids(
        self,
        tenant_id: str,
        user_id: str,
    ) -> list[str]:
        return list(self._get_store(tenant_id, user_id).keys())
