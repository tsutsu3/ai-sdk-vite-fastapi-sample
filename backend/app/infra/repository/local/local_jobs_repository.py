import json
from pathlib import Path

from app.features.jobs.models import JobRecord
from app.features.jobs.ports import JobRepository
from app.infra.mapper.jobs_mapper import job_doc_to_record, job_record_to_doc
from app.infra.model.jobs_model import JobDoc


class LocalJobRepository(JobRepository):
    """Local file-backed job repository."""

    def __init__(self, base_path: Path) -> None:
        self._base_path = base_path

    def _job_dir(self, tenant_id: str, user_id: str) -> Path:
        return self._base_path / "jobs" / tenant_id / user_id

    def _job_path(self, tenant_id: str, user_id: str, job_id: str) -> Path:
        return self._job_dir(tenant_id, user_id) / f"{job_id}.json"

    async def upsert_job(self, record: JobRecord) -> JobRecord:
        job_dir = self._job_dir(record.tenant_id, record.user_id)
        job_dir.mkdir(parents=True, exist_ok=True)
        doc = job_record_to_doc(record)
        path = self._job_path(record.tenant_id, record.user_id, record.job_id)
        payload = doc.model_dump(by_alias=True, exclude_none=True, mode="json")
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return record

    async def list_jobs(
        self,
        tenant_id: str,
        user_id: str,
        limit: int | None = None,
        continuation_token: str | None = None,
    ) -> tuple[list[JobRecord], str | None]:
        job_dir = self._job_dir(tenant_id, user_id)
        if not job_dir.exists():
            return ([], None)
        records: list[JobRecord] = []
        for path in job_dir.glob("*.json"):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if not isinstance(payload, dict):
                continue
            try:
                doc = JobDoc.model_validate(payload)
            except Exception:
                continue
            records.append(job_doc_to_record(doc))
        records.sort(key=lambda record: record.updated_at, reverse=True)
        offset = 0
        if continuation_token:
            try:
                offset = max(int(continuation_token), 0)
            except ValueError:
                offset = 0
        if limit is None:
            return (records, None)
        safe_limit = max(limit, 0)
        sliced = records[offset : offset + safe_limit]
        next_offset = offset + len(sliced)
        next_token = str(next_offset) if next_offset < len(records) else None
        return (sliced, next_token)

    async def get_job(
        self,
        tenant_id: str,
        user_id: str,
        job_id: str,
    ) -> JobRecord | None:
        path = self._job_path(tenant_id, user_id, job_id)
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        if not isinstance(payload, dict):
            return None
        try:
            doc = JobDoc.model_validate(payload)
        except Exception:
            return None
        if doc.user_id != user_id:
            return None
        return job_doc_to_record(doc)
