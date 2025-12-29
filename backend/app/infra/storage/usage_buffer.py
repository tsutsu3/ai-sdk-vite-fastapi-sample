import asyncio
import json
import time
from collections import defaultdict
from pathlib import Path
from typing import Protocol

from app.core.config import AppConfig, UsageBufferBackend
from app.features.usage.models import UsageRecord
from app.features.usage.ports import UsageRepository
from app.shared.time import now_datetime


class UsageBuffer(Protocol):
    """Buffer interface for raw usage logs."""

    async def append(self, record: UsageRecord) -> None:
        """Append a usage record to the buffer."""
        raise NotImplementedError

    async def flush(self) -> None:
        """Flush buffered records to storage."""
        raise NotImplementedError


class BufferedUsageRepository(UsageRepository):
    """Usage repository that writes records to a buffer."""

    def __init__(self, buffer: UsageBuffer) -> None:
        self._buffer = buffer

    async def record_usage(self, record: UsageRecord) -> None:
        await self._buffer.append(record)

    async def flush(self) -> None:
        await self._buffer.flush()


class _BaseUsageBuffer(UsageBuffer):
    def __init__(self, *, flush_max_records: int, flush_interval_seconds: int) -> None:
        self._flush_max_records = max(1, flush_max_records)
        self._flush_interval_seconds = max(1, flush_interval_seconds)
        self._buffer: list[tuple[str, str]] = []
        self._last_flush = time.monotonic()
        self._lock = asyncio.Lock()
        self._counter = 0

    async def append(self, record: UsageRecord) -> None:
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


class LocalUsageBuffer(_BaseUsageBuffer):
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


class AzureBlobUsageBuffer(_BaseUsageBuffer):
    """Azure Blob buffer for raw usage logs."""

    def __init__(
        self,
        config: AppConfig,
        *,
        flush_max_records: int,
        flush_interval_seconds: int,
    ) -> None:
        if not config.azure_blob_endpoint or not config.azure_blob_api_key:
            raise RuntimeError("Azure Blob settings are not configured.")
        super().__init__(
            flush_max_records=flush_max_records,
            flush_interval_seconds=flush_interval_seconds,
        )
        from azure.storage.blob.aio import BlobServiceClient

        self._container_name = config.usage_buffer_blob_container
        self._prefix = config.usage_buffer_blob_prefix.strip("/")
        self._service = BlobServiceClient(
            account_url=config.azure_blob_endpoint,
            credential=config.azure_blob_api_key,
        )
        self._container = self._service.get_container_client(self._container_name)
        self._initialized = False

    async def _ensure_container(self) -> None:
        if self._initialized:
            return
        try:
            await self._container.create_container()
        except Exception:
            pass
        self._initialized = True

    async def _write_lines(self, dt: str, lines: list[str], part_id: str) -> None:
        await self._ensure_container()
        name = f"dt={dt}/part-{part_id}.jsonl"
        if self._prefix:
            name = f"{self._prefix}/{name}"
        data = ("\n".join(lines) + "\n").encode("utf-8")
        await self._container.upload_blob(name=name, data=data, overwrite=False)


class GcsUsageBuffer(_BaseUsageBuffer):
    """GCS buffer for raw usage logs."""

    def __init__(
        self,
        config: AppConfig,
        *,
        flush_max_records: int,
        flush_interval_seconds: int,
    ) -> None:
        if not config.usage_buffer_gcs_bucket:
            raise RuntimeError("GCS bucket is not configured for usage buffering.")
        super().__init__(
            flush_max_records=flush_max_records,
            flush_interval_seconds=flush_interval_seconds,
        )
        try:
            from google.cloud import storage
        except ImportError as exc:
            raise RuntimeError(
                "google-cloud-storage is required for GCP usage buffering."
            ) from exc

        self._bucket_name = config.usage_buffer_gcs_bucket
        self._prefix = config.usage_buffer_gcs_prefix.strip("/")
        self._client = storage.Client()
        self._bucket = self._client.bucket(self._bucket_name)

    async def _write_lines(self, dt: str, lines: list[str], part_id: str) -> None:
        name = f"dt={dt}/part-{part_id}.jsonl"
        if self._prefix:
            name = f"{self._prefix}/{name}"
        data = "\n".join(lines) + "\n"

        def _upload() -> None:
            blob = self._bucket.blob(name)
            blob.upload_from_string(data)

        await asyncio.to_thread(_upload)


def create_usage_buffer(app_config: AppConfig) -> UsageBuffer:
    match app_config.usage_buffer_backend:
        case UsageBufferBackend.local:
            return LocalUsageBuffer(
                app_config.usage_buffer_local_path,
                flush_max_records=app_config.usage_buffer_flush_max_records,
                flush_interval_seconds=app_config.usage_buffer_flush_interval_seconds,
            )
        case UsageBufferBackend.azure:
            return AzureBlobUsageBuffer(
                app_config,
                flush_max_records=app_config.usage_buffer_flush_max_records,
                flush_interval_seconds=app_config.usage_buffer_flush_interval_seconds,
            )
        case UsageBufferBackend.gcp:
            return GcsUsageBuffer(
                app_config,
                flush_max_records=app_config.usage_buffer_flush_max_records,
                flush_interval_seconds=app_config.usage_buffer_flush_interval_seconds,
            )
        case _:
            raise RuntimeError(
                f"Unsupported usage buffer backend: {app_config.usage_buffer_backend}"
            )


def create_usage_repository(app_config: AppConfig) -> UsageRepository:
    return BufferedUsageRepository(create_usage_buffer(app_config))
