import asyncio
import json
import time
from collections import defaultdict
from app.features.usage.models import UsageRecord
from app.features.usage.ports import UsageRepository
from app.shared.time import now_datetime


class BufferedUsageRepositoryBase(UsageRepository):
    """Usage repository that buffers records before writing."""

    def __init__(self, *, flush_max_records: int, flush_interval_seconds: int) -> None:
        self._flush_max_records = max(1, flush_max_records)
        self._flush_interval_seconds = max(1, flush_interval_seconds)
        self._buffer: list[tuple[str, str]] = []
        self._last_flush = time.monotonic()
        self._lock = asyncio.Lock()
        self._counter = 0

    async def record_usage(self, record: UsageRecord) -> None:
        recorded_at = now_datetime()
        dt = recorded_at.date().isoformat()
        payload = record.model_dump()
        payload["recorded_at"] = recorded_at.isoformat()
        payload["dt"] = dt
        line = json.dumps(payload, ensure_ascii=True, separators=(",", ":"))

        async with self._lock:
            self._buffer.append((dt, line))
            should_flush = (
                len(self._buffer) >= self._flush_max_records
                or (time.monotonic() - self._last_flush) >= self._flush_interval_seconds
            )
            if not should_flush:
                return
            items = list(self._buffer)
            self._buffer.clear()
            self._last_flush = time.monotonic()
            self._counter += 1

        await self._flush_items(items, self._counter)

    async def flush(self) -> None:
        async with self._lock:
            if not self._buffer:
                return
            items = list(self._buffer)
            self._buffer.clear()
            self._last_flush = time.monotonic()
            self._counter += 1

        await self._flush_items(items, self._counter)

    async def _flush_items(self, items: list[tuple[str, str]], counter: int) -> None:
        if not items:
            return
        grouped: dict[str, list[str]] = defaultdict(list)
        for dt, line in items:
            grouped[dt].append(line)
        part_id = f"{int(time.time())}-{counter}"
        for dt, lines in grouped.items():
            await self._write_lines(dt, lines, part_id)

    async def _write_lines(self, dt: str, lines: list[str], part_id: str) -> None:
        raise NotImplementedError
