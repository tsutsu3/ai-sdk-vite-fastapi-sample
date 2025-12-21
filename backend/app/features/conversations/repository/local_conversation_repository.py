import json
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
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if payload.get("archived", False):
                continue
            conversations.append(
                ConversationMetadata(
                    id=str(payload.get("id") or path.stem),
                    title=payload.get("title") or DEFAULT_CHAT_TITLE,
                    updatedAt=payload.get("updatedAt") or current_timestamp(),
                    createdAt=payload.get("createdAt"),
                )
            )
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
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if not payload.get("archived", False):
                continue
            conversations.append(
                ConversationMetadata(
                    id=str(payload.get("id") or path.stem),
                    title=payload.get("title") or DEFAULT_CHAT_TITLE,
                    updatedAt=payload.get("updatedAt") or current_timestamp(),
                    createdAt=payload.get("createdAt"),
                )
            )
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
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        return ConversationMetadata(
            id=str(payload.get("id") or conversation_id),
            title=payload.get("title") or DEFAULT_CHAT_TITLE,
            updatedAt=payload.get("updatedAt") or current_timestamp(),
            createdAt=payload.get("createdAt"),
        )

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
                existing = json.loads(path.read_text(encoding="utf-8"))
                existing_created_at = existing.get("createdAt")
            except (OSError, json.JSONDecodeError):
                existing_created_at = None
        payload = {
            "id": conversation_id,
            "title": title or DEFAULT_CHAT_TITLE,
            "updatedAt": updated_at,
            "createdAt": existing_created_at or updated_at,
            "archived": False,
        }
        path.write_text(json.dumps(payload, ensure_ascii=True), encoding="utf-8")
        return ConversationMetadata(
            id=conversation_id,
            title=payload["title"],
            updatedAt=payload["updatedAt"],
            createdAt=payload.get("createdAt"),
        )

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
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        payload["archived"] = archived
        payload["updatedAt"] = updated_at
        path.write_text(json.dumps(payload, ensure_ascii=True), encoding="utf-8")
        return ConversationMetadata(
            id=str(payload.get("id") or conversation_id),
            title=payload.get("title") or DEFAULT_CHAT_TITLE,
            updatedAt=payload.get("updatedAt") or current_timestamp(),
            createdAt=payload.get("createdAt"),
        )

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
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        payload["title"] = title or DEFAULT_CHAT_TITLE
        payload["updatedAt"] = updated_at
        path.write_text(json.dumps(payload, ensure_ascii=True), encoding="utf-8")
        return ConversationMetadata(
            id=str(payload.get("id") or conversation_id),
            title=payload.get("title") or DEFAULT_CHAT_TITLE,
            updatedAt=payload.get("updatedAt") or current_timestamp(),
            createdAt=payload.get("createdAt"),
        )

    async def list_all_conversation_ids(
        self,
        tenant_id: str,
        user_id: str,
    ) -> list[str]:
        conversation_dir = self._conversation_dir(tenant_id, user_id)
        if not conversation_dir.exists():
            return []
        return [path.stem for path in conversation_dir.glob("*.json")]
