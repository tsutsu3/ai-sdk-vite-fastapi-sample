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

    async def get_job(
        self,
        tenant_id: str,
        user_id: str,
        job_id: str,
    ) -> JobRecord | None:
        return self._jobs.get(self._key(tenant_id, user_id, job_id))
