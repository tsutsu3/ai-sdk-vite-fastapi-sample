from typing import Protocol

from app.features.jobs.models import JobRecord


class JobRepository(Protocol):
    """Interface for job persistence."""

    async def upsert_job(self, record: JobRecord) -> JobRecord:
        """Create or update a job record."""
        raise NotImplementedError

    async def get_job(
        self,
        tenant_id: str,
        user_id: str,
        job_id: str,
    ) -> JobRecord | None:
        """Fetch a job record by id."""
        raise NotImplementedError
