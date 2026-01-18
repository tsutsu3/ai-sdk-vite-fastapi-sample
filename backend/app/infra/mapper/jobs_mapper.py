from app.features.jobs.models import JobRecord
from app.infra.model.jobs_model import JobDoc


def job_doc_to_record(doc: JobDoc) -> JobRecord:
    return JobRecord(
        job_id=doc.id,
        tenant_id=doc.tenant_id,
        user_id=doc.user_id,
        conversation_id=doc.conversation_id,
        status=doc.status,
        created_at=doc.created_at,
        updated_at=doc.updated_at or doc.created_at,
    )


def job_record_to_doc(record: JobRecord) -> JobDoc:
    return JobDoc(
        id=record.job_id,
        tenant_id=record.tenant_id,
        user_id=record.user_id,
        conversation_id=record.conversation_id,
        status=record.status,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )
