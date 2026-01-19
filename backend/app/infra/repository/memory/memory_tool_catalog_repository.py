from app.features.tool_catalog.models import DataSourceRecord, ToolRecord
from app.features.tool_catalog.ports import ToolCatalogRepository


class MemoryToolCatalogRepository(ToolCatalogRepository):
    """In-memory tool catalog repository for local/test use."""

    def __init__(
        self,
        *,
        tools: dict[str, dict[str, ToolRecord]] | None = None,
        data_sources: dict[str, dict[str, DataSourceRecord]] | None = None,
    ) -> None:
        self._tools = tools or {}
        self._data_sources = data_sources or {}

    async def get_tool(self, tenant_id: str, tool_id: str) -> ToolRecord | None:
        return (self._tools.get(tenant_id) or {}).get(tool_id)

    async def list_tools(self, tenant_id: str) -> list[ToolRecord]:
        return list((self._tools.get(tenant_id) or {}).values())

    async def save_tool(self, record: ToolRecord) -> None:
        self._tools.setdefault(record.tenant_id, {})[record.id] = record

    async def get_data_source(
        self, tenant_id: str, data_source_id: str
    ) -> DataSourceRecord | None:
        return (self._data_sources.get(tenant_id) or {}).get(data_source_id)

    async def list_data_sources(self, tenant_id: str) -> list[DataSourceRecord]:
        return list((self._data_sources.get(tenant_id) or {}).values())

    async def save_data_source(self, record: DataSourceRecord) -> None:
        self._data_sources.setdefault(record.tenant_id, {})[record.id] = record
