from pathlib import Path

from app.infra.storage.usage_buffer.base import BufferedUsageRepositoryBase


class LocalUsageRepository(BufferedUsageRepositoryBase):
    """Local file buffer for raw usage logs."""

    def __init__(
        self, base_path: str, *, flush_max_records: int, flush_interval_seconds: int
    ) -> None:
        super().__init__(
            flush_max_records=flush_max_records,
            flush_interval_seconds=flush_interval_seconds,
        )
        self._base_path = Path(base_path).resolve()

    async def _write_lines(self, dt: str, lines: list[str], part_id: str) -> None:
        target_dir = self._base_path / f"dt={dt}"
        target_dir.mkdir(parents=True, exist_ok=True)
        path = target_dir / f"part-{part_id}.jsonl"
        content = "\n".join(lines) + "\n"
        path.write_text(content, encoding="utf-8")
