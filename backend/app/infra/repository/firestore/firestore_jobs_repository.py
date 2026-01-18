import base64
import json
from datetime import datetime
from logging import getLogger

from google.cloud import firestore

from app.features.jobs.models import JobRecord
from app.features.jobs.ports import JobRepository
from app.infra.mapper.jobs_mapper import job_doc_to_record, job_record_to_doc
from app.infra.model.jobs_model import JobDoc
from app.shared.time import now_datetime

logger = getLogger(__name__)


class FirestoreJobRepository(JobRepository):
    """Firestore-backed job repository."""

    def __init__(self, collection) -> None:
        self._collection = collection
        logger.info("firestore.jobs.ready collection=%s", collection.id)

    def _doc_id(self, tenant_id: str, user_id: str, job_id: str) -> str:
        return f"{tenant_id}:{user_id}:{job_id}"

    def _encode_cursor(self, updated_at: datetime, job_id: str) -> str:
        payload = {"updatedAt": updated_at.isoformat(), "id": job_id}
        raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
        return base64.urlsafe_b64encode(raw).decode("ascii")

    def _decode_cursor(self, token: str | None) -> tuple[datetime, str] | None:
        if not token:
            return None
        try:
            raw = base64.urlsafe_b64decode(token.encode("ascii"))
            payload = json.loads(raw.decode("utf-8"))
            updated_at = datetime.fromisoformat(payload["updatedAt"])
            job_id = str(payload["id"])
            return updated_at, job_id
        except Exception:
            logger.debug("firestore.jobs.invalid_cursor token=%s", token)
            return None

    async def upsert_job(self, record: JobRecord) -> JobRecord:
        updated = record.model_copy(update={"updated_at": now_datetime()})
        doc_id = self._doc_id(updated.tenant_id, updated.user_id, updated.job_id)
        doc = job_record_to_doc(updated)
        await self._collection.document(doc_id).set(
            doc.model_dump(by_alias=True, exclude_none=True)
        )
        return updated

    async def list_jobs(
        self,
        tenant_id: str,
        user_id: str,
        limit: int | None = None,
        continuation_token: str | None = None,
    ) -> tuple[list[JobRecord], str | None]:
        query = (
            self._collection.where("tenantId", "==", tenant_id)
            .where("userId", "==", user_id)
            .order_by("updatedAt", direction=firestore.Query.DESCENDING)
            .order_by("id", direction=firestore.Query.DESCENDING)
        )
        cursor = self._decode_cursor(continuation_token)
        if cursor:
            query = query.start_after([cursor[0], cursor[1]])
        if limit is not None:
            query = query.limit(limit)
        results: list[JobRecord] = []
        async for doc in query.stream():
            try:
                item = JobDoc.model_validate(doc.to_dict())
            except Exception:
                continue
            results.append(job_doc_to_record(item))
        next_token = None
        if limit is not None and len(results) == limit:
            last = results[-1]
            last_updated = last.updated_at or last.created_at
            next_token = self._encode_cursor(last_updated, last.job_id)
        return (results, next_token)

    async def get_job(
        self,
        tenant_id: str,
        user_id: str,
        job_id: str,
    ) -> JobRecord | None:
        doc_id = self._doc_id(tenant_id, user_id, job_id)
        doc = await self._collection.document(doc_id).get()
        if not doc.exists:
            return None
        try:
            item = JobDoc.model_validate(doc.to_dict())
        except Exception:
            return None
        if item.user_id != user_id:
            return None
        return job_doc_to_record(item)
