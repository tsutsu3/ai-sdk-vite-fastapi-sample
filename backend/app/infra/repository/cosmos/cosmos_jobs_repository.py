from azure.cosmos.aio import ContainerProxy

from app.features.jobs.models import JobRecord
from app.features.jobs.ports import JobRepository
from app.infra.mapper.jobs_mapper import job_doc_to_record, job_record_to_doc
from app.infra.model.jobs_model import JobDoc
from app.shared.time import now_datetime


def job_partition(tenant_id: str) -> str:
    return tenant_id


class CosmosJobRepository(JobRepository):
    """Cosmos DB job repository."""

    def __init__(self, container: ContainerProxy) -> None:
        self._container = container

    async def upsert_job(self, record: JobRecord) -> JobRecord:
        updated = record.model_copy(update={"updated_at": now_datetime()})
        doc = job_record_to_doc(updated)
        await self._container.upsert_item(
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
        pk = job_partition(tenant_id)
        query = (
            "SELECT * FROM c WHERE c.userId = @userId "
            "ORDER BY c.updatedAt DESC"
        )
        parameters = [{"name": "@userId", "value": user_id}]
        results: list[JobRecord] = []
        next_token: str | None = None
        if limit is None:
            items = self._container.query_items(
                query=query,
                parameters=parameters,
                partition_key=pk,
            )
            async for item in items:
                try:
                    results.append(job_doc_to_record(JobDoc.model_validate(item)))
                except Exception:
                    continue
            return (results, None)
        items = self._container.query_items(
            query=query,
            parameters=parameters,
            partition_key=pk,
            max_item_count=limit,
        )
        page_iter = items.by_page(continuation_token=continuation_token)
        async for page in page_iter:
            async for item in page:
                try:
                    results.append(job_doc_to_record(JobDoc.model_validate(item)))
                except Exception:
                    continue
            next_token = page_iter.continuation_token
            break
        return (results, next_token)

    async def get_job(
        self,
        tenant_id: str,
        user_id: str,
        job_id: str,
    ) -> JobRecord | None:
        pk = job_partition(tenant_id)
        try:
            item = await self._container.read_item(item=job_id, partition_key=pk)
        except Exception:
            return None
        try:
            doc = JobDoc.model_validate(item)
        except Exception:
            return None
        if doc.user_id != user_id:
            return None
        return job_doc_to_record(doc)
