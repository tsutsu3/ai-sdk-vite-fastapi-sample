from pathlib import Path

from app.features.conversations.models import ConversationRecord
from app.features.conversations.ports import ConversationRepository
from app.infra.mapper.conversations_mapper import (
    conversation_doc_to_record,
    conversation_record_to_doc,
)
from app.infra.model.conversations_model import ConversationDoc
from app.shared.constants import DEFAULT_CHAT_TITLE
from app.shared.time import now_datetime


class LocalConversationRepository(ConversationRepository):
    def __init__(self, base_path: Path) -> None:
        self._base_path = base_path

    def _conversation_dir(self, tenant_id: str, user_id: str) -> Path:
        """Resolve the directory for a user's conversations.

        Args:
            tenant_id: Tenant identifier.
            user_id: User identifier.

        Returns:
            Path: Directory path for the user's conversations.
        """
        return self._base_path / "conversations" / tenant_id / user_id

    async def list_conversations(
        self,
        tenant_id: str,
        user_id: str,
        limit: int | None = None,
        continuation_token: str | None = None,
    ) -> tuple[list[ConversationRecord], str | None]:
        conversation_dir = self._conversation_dir(tenant_id, user_id)
        if not conversation_dir.exists():
            return ([], None)
        conversations: list[ConversationRecord] = []
        for path in conversation_dir.glob("*.json"):
            try:
                metadata = ConversationDoc.model_validate_json(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if metadata.archived:
                continue
            conversations.append(conversation_doc_to_record(metadata))
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
        conversation_dir = self._conversation_dir(tenant_id, user_id)
        if not conversation_dir.exists():
            return ([], None)
        conversations: list[ConversationRecord] = []
        for path in conversation_dir.glob("*.json"):
            try:
                metadata = ConversationDoc.model_validate_json(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if not metadata.archived:
                continue
            conversations.append(conversation_doc_to_record(metadata))
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
        path = self._conversation_dir(tenant_id, user_id) / f"{conversation_id}.json"
        if not path.exists():
            return None
        try:
            doc = ConversationDoc.model_validate_json(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        return conversation_doc_to_record(doc)

    async def upsert_conversation(
        self,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
        title: str,
    ) -> ConversationRecord:
        updated_at = now_datetime()
        conversation_dir = self._conversation_dir(tenant_id, user_id)
        conversation_dir.mkdir(parents=True, exist_ok=True)
        path = conversation_dir / f"{conversation_id}.json"
        existing_created_at = None
        if path.exists():
            try:
                existing = ConversationDoc.model_validate_json(path.read_text(encoding="utf-8"))
                existing_created_at = existing.created_at
            except (OSError, ValueError):
                existing_created_at = None
        metadata = ConversationRecord(
            id=conversation_id,
            title=title or DEFAULT_CHAT_TITLE,
            archived=False,
            updatedAt=updated_at,
            createdAt=existing_created_at or updated_at,
        )
        doc = conversation_record_to_doc(
            metadata,
            tenant_id=tenant_id,
            user_id=user_id,
            tool_id="chat",
        )
        path.write_text(doc.model_dump_json(), encoding="utf-8")
        return metadata

    async def archive_conversation(
        self,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
        archived: bool,
    ) -> ConversationRecord | None:
        conversation_dir = self._conversation_dir(tenant_id, user_id)
        path = conversation_dir / f"{conversation_id}.json"
        if not path.exists():
            return None
        updated_at = now_datetime()
        try:
            metadata = ConversationDoc.model_validate_json(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        updated = metadata.model_copy(update={"archived": archived, "updated_at": updated_at})
        path.write_text(updated.model_dump_json(), encoding="utf-8")
        return conversation_doc_to_record(updated)

    async def delete_conversation(
        self,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
    ) -> bool:
        path = self._conversation_dir(tenant_id, user_id) / f"{conversation_id}.json"
        if not path.exists():
            return False
        try:
            path.unlink()
        except OSError:
            return False
        return True

    async def update_title(
        self,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
        title: str,
    ) -> ConversationRecord | None:
        conversation_dir = self._conversation_dir(tenant_id, user_id)
        path = conversation_dir / f"{conversation_id}.json"
        if not path.exists():
            return None
        updated_at = now_datetime()
        try:
            metadata = ConversationDoc.model_validate_json(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        updated = metadata.model_copy(
            update={
                "title": title or DEFAULT_CHAT_TITLE,
                "updated_at": updated_at,
            }
        )
        path.write_text(updated.model_dump_json(), encoding="utf-8")
        return conversation_doc_to_record(updated)

    async def list_all_conversation_ids(
        self,
        tenant_id: str,
        user_id: str,
    ) -> list[str]:
        conversation_dir = self._conversation_dir(tenant_id, user_id)
        if not conversation_dir.exists():
            return []
        return [path.stem for path in conversation_dir.glob("*.json")]
