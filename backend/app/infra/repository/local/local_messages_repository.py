import json
from pathlib import Path

from app.features.messages.models import MessageRecord
from app.features.messages.ports import MessageRepository
from app.infra.mapper.messages_mapper import (
    message_doc_to_record,
    message_record_to_doc,
)
from app.infra.model.messages_model import MessageDoc
from app.shared.time import now_datetime


class LocalMessageRepository(MessageRepository):
    def __init__(self, base_path: Path) -> None:
        self._base_path = base_path

    def _message_dir(self, tenant_id: str, user_id: str) -> Path:
        """Resolve the directory for stored messages.

        Args:
            tenant_id: Tenant identifier.
            user_id: User identifier.

        Returns:
            Path: Directory path for tenant/user messages.
        """
        return self._base_path / "messages" / tenant_id / user_id

    async def list_messages(
        self,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
        limit: int | None = None,
        continuation_token: str | None = None,
        descending: bool = False,
    ) -> tuple[list[MessageRecord], str | None]:
        path = self._message_dir(tenant_id, user_id) / f"{conversation_id}.json"
        if not path.exists():
            return ([], None)
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return ([], None)
        if not isinstance(payload, list):
            return ([], None)
        results: list[MessageRecord] = []
        for item in payload:
            if not isinstance(item, dict):
                continue
            try:
                results.append(message_doc_to_record(MessageDoc.model_validate(item)))
            except Exception:
                continue
        if descending:
            results = list(reversed(results))
        if limit is None:
            return (results, None)
        safe_limit = max(limit, 0)
        safe_offset = 0
        if continuation_token:
            try:
                safe_offset = max(int(continuation_token), 0)
            except ValueError:
                safe_offset = 0
        sliced = results[safe_offset : safe_offset + safe_limit]
        next_offset = safe_offset + len(sliced)
        next_token = str(next_offset) if next_offset < len(results) else None
        return (sliced, next_token)

    async def upsert_messages(
        self,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
        messages: list[MessageRecord],
    ) -> list[MessageRecord]:
        message_dir = self._message_dir(tenant_id, user_id)
        message_dir.mkdir(parents=True, exist_ok=True)
        path = message_dir / f"{conversation_id}.json"
        existing: list[MessageRecord] = []
        if path.exists():
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                payload = []
            if isinstance(payload, list):
                for item in payload:
                    if not isinstance(item, dict):
                        continue
                    try:
                        existing.append(message_doc_to_record(MessageDoc.model_validate(item)))
                    except Exception:
                        continue
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
        payload = [
            message_record_to_doc(
                message,
                tenant_id=tenant_id,
                user_id=user_id,
                conversation_id=conversation_id,
                tool_id="chat",
            ).model_dump(by_alias=True, exclude_none=True, mode="json")
            for message in existing
        ]
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return list(messages)

    async def delete_messages(self, tenant_id: str, user_id: str, conversation_id: str) -> None:
        path = self._message_dir(tenant_id, user_id) / f"{conversation_id}.json"
        if path.exists():
            try:
                path.unlink()
            except OSError:
                pass

    async def update_message_reaction(
        self,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
        message_id: str,
        reaction: str | None,
    ) -> MessageRecord | None:
        path = self._message_dir(tenant_id, user_id) / f"{conversation_id}.json"
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        if not isinstance(payload, list):
            return None
        updated: MessageRecord | None = None
        messages: list[MessageRecord] = []
        for item in payload:
            if not isinstance(item, dict):
                continue
            try:
                doc = MessageDoc.model_validate(item)
            except Exception:
                continue
            if doc.id == message_id:
                doc = doc.model_copy(update={"reaction": reaction})
                updated = message_doc_to_record(doc)
            messages.append(message_doc_to_record(doc))
        if updated is None:
            return None
        payload = [
            message_record_to_doc(
                message,
                tenant_id=tenant_id,
                user_id=user_id,
                conversation_id=conversation_id,
                tool_id="chat",
            ).model_dump(by_alias=True, exclude_none=True, mode="json")
            for message in messages
        ]
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return updated
