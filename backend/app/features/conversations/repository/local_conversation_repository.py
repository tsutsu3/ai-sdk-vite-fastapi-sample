from datetime import datetime, timezone
from pathlib import Path

from app.features.conversations.models import ConversationMetadata
from app.features.conversations.ports import ConversationRepository
from app.shared.constants import DEFAULT_CHAT_TITLE


def current_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


class LocalConversationRepository(ConversationRepository):
    def __init__(self, base_path: Path) -> None:
        self._base_path = base_path

    def _conversation_dir(self, tenant_id: str, user_id: str) -> Path:
        return self._base_path / "conversations" / tenant_id / user_id

    async def list_conversations(
        self,
        tenant_id: str,
        user_id: str,
    ) -> list[ConversationMetadata]:
        conversation_dir = self._conversation_dir(tenant_id, user_id)
        if not conversation_dir.exists():
            return []
        conversations: list[ConversationMetadata] = []
        for path in conversation_dir.glob("*.json"):
            try:
                metadata = ConversationMetadata.model_validate_json(
                    path.read_text(encoding="utf-8")
                )
            except (OSError, ValueError):
                continue
            if metadata.archived:
                continue
            conversations.append(metadata)
        return conversations

    async def list_archived_conversations(
        self,
        tenant_id: str,
        user_id: str,
    ) -> list[ConversationMetadata]:
        conversation_dir = self._conversation_dir(tenant_id, user_id)
        if not conversation_dir.exists():
            return []
        conversations: list[ConversationMetadata] = []
        for path in conversation_dir.glob("*.json"):
            try:
                metadata = ConversationMetadata.model_validate_json(
                    path.read_text(encoding="utf-8")
                )
            except (OSError, ValueError):
                continue
            if not metadata.archived:
                continue
            conversations.append(metadata)
        return conversations

    async def get_conversation(
        self,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
    ) -> ConversationMetadata | None:
        path = self._conversation_dir(tenant_id, user_id) / f"{conversation_id}.json"
        if not path.exists():
            return None
        try:
            return ConversationMetadata.model_validate_json(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None

    async def upsert_conversation(
        self,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
        title: str,
        updated_at: str,
    ) -> ConversationMetadata:
        conversation_dir = self._conversation_dir(tenant_id, user_id)
        conversation_dir.mkdir(parents=True, exist_ok=True)
        path = conversation_dir / f"{conversation_id}.json"
        existing_created_at = None
        if path.exists():
            try:
                existing = ConversationMetadata.model_validate_json(
                    path.read_text(encoding="utf-8")
                )
                existing_created_at = existing.createdAt
            except (OSError, ValueError):
                existing_created_at = None
        metadata = ConversationMetadata(
            id=conversation_id,
            title=title or DEFAULT_CHAT_TITLE,
            archived=False,
            updatedAt=updated_at,
            createdAt=existing_created_at or updated_at,
        )
        path.write_text(metadata.model_dump_json(), encoding="utf-8")
        return metadata

    async def archive_conversation(
        self,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
        archived: bool,
        updated_at: str,
    ) -> ConversationMetadata | None:
        conversation_dir = self._conversation_dir(tenant_id, user_id)
        path = conversation_dir / f"{conversation_id}.json"
        if not path.exists():
            return None
        try:
            metadata = ConversationMetadata.model_validate_json(
                path.read_text(encoding="utf-8")
            )
        except (OSError, ValueError):
            return None
        updated = metadata.model_copy(update={"archived": archived, "updatedAt": updated_at})
        path.write_text(updated.model_dump_json(), encoding="utf-8")
        return updated

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
        updated_at: str,
    ) -> ConversationMetadata | None:
        conversation_dir = self._conversation_dir(tenant_id, user_id)
        path = conversation_dir / f"{conversation_id}.json"
        if not path.exists():
            return None
        try:
            metadata = ConversationMetadata.model_validate_json(
                path.read_text(encoding="utf-8")
            )
        except (OSError, ValueError):
            return None
        updated = metadata.model_copy(
            update={
                "title": title or DEFAULT_CHAT_TITLE,
                "updatedAt": updated_at,
            }
        )
        path.write_text(updated.model_dump_json(), encoding="utf-8")
        return updated

    async def list_all_conversation_ids(
        self,
        tenant_id: str,
        user_id: str,
    ) -> list[str]:
        conversation_dir = self._conversation_dir(tenant_id, user_id)
        if not conversation_dir.exists():
            return []
        return [path.stem for path in conversation_dir.glob("*.json")]
