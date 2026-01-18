from app.features.jobs.models import JobRecord
from app.features.jobs.ports import JobRepository


class MemoryJobRepository(JobRepository):
    """In-memory job repository (local/test)."""

    def __init__(self) -> None:
        self._jobs: dict[str, JobRecord] = {}

    def _key(self, tenant_id: str, user_id: str, job_id: str) -> str:
        return f"{tenant_id}:{user_id}:{job_id}"

    async def upsert_job(self, record: JobRecord) -> JobRecord:
        key = self._key(record.tenant_id, record.user_id, record.job_id)
        self._jobs[key] = record
        return record

    async def list_jobs(
        self,
        tenant_id: str,
        user_id: str,
        limit: int | None = None,
        continuation_token: str | None = None,
    ) -> tuple[list[JobRecord], str | None]:
        items = [
            record
            for record in self._jobs.values()
            if record.tenant_id == tenant_id and record.user_id == user_id
        ]
        items.sort(key=lambda record: record.updated_at, reverse=True)
        offset = 0
        if continuation_token:
            try:
                offset = max(int(continuation_token), 0)
            except ValueError:
                offset = 0
        if limit is None:
            return (items, None)
        safe_limit = max(limit, 0)
        sliced = items[offset : offset + safe_limit]
        next_offset = offset + len(sliced)
        next_token = str(next_offset) if next_offset < len(items) else None
        return (sliced, next_token)

    async def get_job(
        self,
        tenant_id: str,
        user_id: str,
        job_id: str,
    ) -> JobRecord | None:
        return self._jobs.get(self._key(tenant_id, user_id, job_id))
