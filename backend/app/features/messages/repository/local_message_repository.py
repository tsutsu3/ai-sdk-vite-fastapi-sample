import json
from pathlib import Path

from app.features.messages.ports import MessageRepository


class LocalMessageRepository(MessageRepository):
    def __init__(self, base_path: Path) -> None:
        self._base_path = base_path

    def _message_dir(self, tenant_id: str) -> Path:
        return self._base_path / "messages" / tenant_id

    async def list_messages(self, tenant_id: str, conversation_id: str) -> list[dict]:
        path = self._message_dir(tenant_id) / f"{conversation_id}.json"
        if not path.exists():
            return []
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        return list(payload) if isinstance(payload, list) else []

    async def upsert_messages(
        self,
        tenant_id: str,
        conversation_id: str,
        messages: list[dict],
    ) -> None:
        message_dir = self._message_dir(tenant_id)
        message_dir.mkdir(parents=True, exist_ok=True)
        path = message_dir / f"{conversation_id}.json"
        path.write_text(json.dumps(messages, ensure_ascii=True), encoding="utf-8")

    async def delete_messages(self, tenant_id: str, conversation_id: str) -> None:
        path = self._message_dir(tenant_id) / f"{conversation_id}.json"
        if path.exists():
            try:
                path.unlink()
            except OSError:
                pass
