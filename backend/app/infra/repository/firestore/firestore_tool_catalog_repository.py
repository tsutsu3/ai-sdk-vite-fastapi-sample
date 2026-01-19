from logging import getLogger

from app.features.tool_catalog.models import DataSourceRecord, ToolRecord
from app.features.tool_catalog.ports import ToolCatalogRepository
from app.infra.mapper.tool_catalog_mapper import (
    data_source_doc_to_record,
    data_source_record_to_doc,
    tool_doc_to_record,
    tool_record_to_doc,
)
from app.infra.model.tool_catalog_model import DataSourceDoc, ToolDoc

logger = getLogger(__name__)


class FirestoreToolCatalogRepository(ToolCatalogRepository):
    """Firestore-backed repository for tenant tool catalogs."""

    def __init__(self, tenants_collection) -> None:
        self._tenants = tenants_collection

    def _tools(self, tenant_id: str):
        return self._tenants.document(tenant_id).collection("tools")

    def _data_sources(self, tenant_id: str):
        return self._tenants.document(tenant_id).collection("data_sources")

    async def get_tool(self, tenant_id: str, tool_id: str) -> ToolRecord | None:
        doc = await self._tools(tenant_id).document(tool_id).get()
        if not doc.exists:
            return None
        try:
            return tool_doc_to_record(ToolDoc.model_validate(doc.to_dict()))
        except Exception:
            return None

    async def list_tools(self, tenant_id: str) -> list[ToolRecord]:
        results: list[ToolRecord] = []
        async for doc in self._tools(tenant_id).stream():
            try:
                results.append(tool_doc_to_record(ToolDoc.model_validate(doc.to_dict())))
            except Exception:
                continue
        return results

    async def save_tool(self, record: ToolRecord) -> None:
        doc = tool_record_to_doc(record)
        await self._tools(record.tenant_id).document(record.id).set(
            doc.model_dump(by_alias=True, exclude_none=True)
        )

    async def get_data_source(
        self, tenant_id: str, data_source_id: str
    ) -> DataSourceRecord | None:
        doc = await self._data_sources(tenant_id).document(data_source_id).get()
        if not doc.exists:
            return None
        try:
            return data_source_doc_to_record(DataSourceDoc.model_validate(doc.to_dict()))
        except Exception:
            return None

    async def list_data_sources(self, tenant_id: str) -> list[DataSourceRecord]:
        results: list[DataSourceRecord] = []
        async for doc in self._data_sources(tenant_id).stream():
            try:
                results.append(
                    data_source_doc_to_record(DataSourceDoc.model_validate(doc.to_dict()))
                )
            except Exception:
                continue
        return results

    async def save_data_source(self, record: DataSourceRecord) -> None:
        doc = data_source_record_to_doc(record)
        await self._data_sources(record.tenant_id).document(record.id).set(
            doc.model_dump(by_alias=True, exclude_none=True)
        )
