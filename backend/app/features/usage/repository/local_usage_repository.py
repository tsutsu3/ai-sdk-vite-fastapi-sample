import json
from pathlib import Path

from app.features.usage.models import UsageRecord
from app.features.usage.ports import UsageRepository


class LocalUsageRepository(UsageRepository):
    def __init__(self, base_path: Path) -> None:
        self._base_path = base_path

    def _usage_path(self, tenant_id: str, user_id: str) -> Path:
        return self._base_path / "usage" / tenant_id / f"{user_id}.jsonl"

    async def record_usage(self, record: UsageRecord) -> None:
        path = self._usage_path(record.tenant_id, record.user_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(record.model_dump(), ensure_ascii=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(f"{line}\n")
