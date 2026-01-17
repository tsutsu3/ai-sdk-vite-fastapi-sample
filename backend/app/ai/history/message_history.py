import logging
import uuid
from typing import Iterable

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from app.ai.models import HistoryKey
from app.features.messages.models import MessagePartRecord, MessageRecord
from app.features.messages.ports import MessageRepository
from app.shared.time import now_datetime

logger = logging.getLogger(__name__)


def serialize_history_key(key: HistoryKey) -> str:
    return f"{key.tenant_id}::{key.user_id}::{key.conversation_id}"


def parse_history_key(session_id: str) -> HistoryKey:
    parts = session_id.split("::", 2)
    if len(parts) != 3:
        raise ValueError("Invalid session_id format.")
    tenant_id, user_id, conversation_id = (value.strip() for value in parts)
    if not (tenant_id and user_id and conversation_id):
        raise ValueError("Invalid session_id format.")
    return HistoryKey(tenant_id=tenant_id, user_id=user_id, conversation_id=conversation_id)


class RepositoryChatMessageHistory(BaseChatMessageHistory):
    def __init__(
        self,
        repo: MessageRepository,
        key: HistoryKey,
        *,
        window_size: int | None,
        write_enabled: bool = True,
    ):
        self._repo = repo
        self._key = key
        self._window_size = window_size
        self._write_enabled = write_enabled

    @property
    def messages(self) -> list[BaseMessage]:
        raise NotImplementedError("Use aget_messages for async access.")

    def clear(self) -> None:
        raise RuntimeError("Use aclear for async access.")

    async def aget_messages(self) -> list[BaseMessage]:
        limit = self._window_size
        descending = bool(limit)
        logger.debug(
            "history.fetch tenant_id=%s user_id=%s conversation_id=%s limit=%s descending=%s",
            self._key.tenant_id,
            self._key.user_id,
            self._key.conversation_id,
            limit,
            descending,
        )
        records, _ = await self._repo.list_messages(
            self._key.tenant_id,
            self._key.user_id,
            self._key.conversation_id,
            limit=limit,
            continuation_token=None,
            descending=descending,
        )
        logger.debug(
            "history.fetch.done tenant_id=%s user_id=%s conversation_id=%s count=%s",
            self._key.tenant_id,
            self._key.user_id,
            self._key.conversation_id,
            len(records),
        )
        if descending:
            records = list(reversed(records))
        return _messages_from_records(records)

    async def aadd_message(self, message: BaseMessage) -> None:
        if not self._write_enabled:
            return
        await self._repo.upsert_messages(
            self._key.tenant_id,
            self._key.user_id,
            self._key.conversation_id,
            [_record_from_message(message)],
        )

    async def aadd_messages(self, messages: Iterable[BaseMessage]) -> None:
        if not self._write_enabled:
            return
        records = [_record_from_message(message) for message in messages]
        if not records:
            return
        await self._repo.upsert_messages(
            self._key.tenant_id,
            self._key.user_id,
            self._key.conversation_id,
            records,
        )

    async def aclear(self) -> None:
        if not self._write_enabled:
            return
        await self._repo.delete_messages(
            self._key.tenant_id,
            self._key.user_id,
            self._key.conversation_id,
        )


def _record_from_message(message: BaseMessage) -> MessageRecord:
    if isinstance(message, HumanMessage):
        role = "user"
    elif isinstance(message, AIMessage):
        role = "assistant"
    elif isinstance(message, SystemMessage):
        role = "system"
    else:
        role = "user"
    return MessageRecord(
        id=f"msg-{uuid.uuid4()}",
        role=role,
        parts=[MessagePartRecord(type="text", text=str(message.content))],
        created_at=now_datetime(),
        parent_message_id="",
    )


def _messages_from_records(records: Iterable[MessageRecord]) -> list[BaseMessage]:
    converted: list[BaseMessage] = []
    for record in records:
        text_parts = [part.text or "" for part in record.parts if part.type == "text"]
        content = " ".join(part.strip() for part in text_parts if part).strip()
        if not content:
            continue
        if record.role == "system":
            converted.append(SystemMessage(content=content))
        elif record.role == "assistant":
            converted.append(AIMessage(content=content))
        else:
            converted.append(HumanMessage(content=content))
    return converted
