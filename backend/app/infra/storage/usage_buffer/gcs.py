import asyncio
import json
import time

from app.core.config import AppConfig
from app.features.usage.models import UsageRecord
from app.features.usage.ports import UsageRepository
from app.shared.time import now_datetime


class GcsUsageRepository(UsageRepository):
    """GCS usage repository (no local buffering)."""

    def __init__(
        self,
        config: AppConfig,
    ) -> None:
        if not config.usage_buffer_gcs_bucket:
            raise RuntimeError("GCS bucket is not configured for usage buffering.")
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
            self._counter += 1
            part_id = f"{int(time.time())}-{self._counter}"

        name = f"dt={dt}/part-{part_id}.jsonl"
        if self._prefix:
            name = f"{self._prefix}/{name}"
        data = line + "\n"

        def _upload() -> None:
            blob = self._bucket.blob(name)
            blob.upload_from_string(data)

        await asyncio.to_thread(_upload)

    async def flush(self) -> None:
        return None
