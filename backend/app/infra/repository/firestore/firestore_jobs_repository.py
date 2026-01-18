from logging import getLogger

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

    async def upsert_job(self, record: JobRecord) -> JobRecord:
        updated = record.model_copy(update={"updated_at": now_datetime()})
        doc_id = self._doc_id(updated.tenant_id, updated.user_id, updated.job_id)
        doc = job_record_to_doc(updated)
        await self._collection.document(doc_id).set(
            doc.model_dump(by_alias=True, exclude_none=True)
        )
        return updated

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
