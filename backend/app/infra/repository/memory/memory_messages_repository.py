from app.features.messages.models import MessagePartRecord, MessageRecord
from app.features.messages.ports import MessageRepository
from app.shared.time import now_datetime


class MemoryMessageRepository(MessageRepository):
    def __init__(self) -> None:
        self._store: dict[tuple[str, str, str], list[MessageRecord]] = {}
        self._store[("default", "user-1", "conv-quickstart")] = [
            MessageRecord(
                id="msg-system",
                role="system",
                parts=[
                    MessagePartRecord(type="text", text="You are a helpful project assistant.")
                ],
                created_at=now_datetime(),
                parent_message_id="",
            ),
            MessageRecord(
                id="msg-user-1",
                role="user",
                parts=[
                    MessagePartRecord(
                        type="text",
                        text="Please outline the next steps for our AI SDK demo.",
                    )
                ],
                created_at=now_datetime(),
                parent_message_id="",
            ),
            MessageRecord(
                id="msg-assistant-1",
                role="assistant",
                parts=[
                    MessagePartRecord(
                        type="text",
                        text="Sure! I will list the milestones and owners so you can start quickly.",
                    )
                ],
                created_at=now_datetime(),
                parent_message_id="",
            ),
        ]
        self._store[("default", "user-1", "conv-rag")] = [
            MessageRecord(
                id="msg-user-2",
                role="user",
                parts=[
                    MessagePartRecord(
                        type="text",
                        text="How can we improve retrieval quality for the docs index?",
                    )
                ],
                created_at=now_datetime(),
                parent_message_id="",
            ),
            MessageRecord(
                id="msg-assistant-2",
                role="assistant",
                parts=[
                    MessagePartRecord(
                        type="text",
                        text="Consider adding hierarchical chunking and reranking with a cross-encoder.",
                    )
                ],
                created_at=now_datetime(),
                parent_message_id="",
            ),
        ]

    async def list_messages(
        self,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
        limit: int | None = None,
        continuation_token: str | None = None,
        descending: bool = False,
    ) -> tuple[list[MessageRecord], str | None]:
        messages = list(self._store.get((tenant_id, user_id, conversation_id), []))
        if descending:
            messages = list(reversed(messages))
        if limit is None:
            return (messages, None)
        safe_limit = max(limit, 0)
        safe_offset = 0
        if continuation_token:
            try:
                safe_offset = max(int(continuation_token), 0)
            except ValueError:
                safe_offset = 0
        sliced = messages[safe_offset : safe_offset + safe_limit]
        next_offset = safe_offset + len(sliced)
        next_token = str(next_offset) if next_offset < len(messages) else None
        return (sliced, next_token)

    async def upsert_messages(
        self,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
        messages: list[MessageRecord],
    ) -> list[MessageRecord]:
        key = (tenant_id, user_id, conversation_id)
        existing = list(self._store.get(key, []))
        index_by_id = {message.id: idx for idx, message in enumerate(existing)}
        for message in messages:
            if message.id in index_by_id:
                previous = existing[index_by_id[message.id]]
                created_at = message.created_at or previous.created_at
                parent_message_id = (
                    message.parent_message_id
                    if message.parent_message_id is not None
                    else previous.parent_message_id
                )
                if created_at is None:
                    created_at = now_datetime()
                if parent_message_id is None:
                    parent_message_id = ""
                if (
                    created_at != message.created_at
                    or parent_message_id != message.parent_message_id
                ):
                    message = message.model_copy(
                        update={
                            "created_at": created_at,
                            "parent_message_id": parent_message_id,
                        }
                    )
                existing[index_by_id[message.id]] = message
            else:
                created_at = message.created_at or now_datetime()
                parent_message_id = (
                    message.parent_message_id if message.parent_message_id is not None else ""
                )
                if (
                    created_at != message.created_at
                    or parent_message_id != message.parent_message_id
                ):
                    message = message.model_copy(
                        update={
                            "created_at": created_at,
                            "parent_message_id": parent_message_id,
                        }
                    )
                index_by_id[message.id] = len(existing)
                existing.append(message)
        self._store[key] = existing
        return list(messages)

    async def delete_messages(self, tenant_id: str, user_id: str, conversation_id: str) -> None:
        self._store.pop((tenant_id, user_id, conversation_id), None)

    async def update_message_reaction(
        self,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
        message_id: str,
        reaction: str | None,
    ) -> MessageRecord | None:
        key = (tenant_id, user_id, conversation_id)
        messages = self._store.get(key)
        if not messages:
            return None
        updated: MessageRecord | None = None
        next_messages: list[MessageRecord] = []
        for message in messages:
            if message.id == message_id:
                message = message.model_copy(update={"reaction": reaction})
                updated = message
            next_messages.append(message)
        if updated is None:
            return None
        self._store[key] = next_messages
        return updated
