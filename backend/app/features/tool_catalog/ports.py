from typing import Protocol

from app.features.tool_catalog.models import DataSourceRecord, ToolRecord


class ToolCatalogRepository(Protocol):
    """Tool catalog repository for tenant-scoped tool definitions."""

    async def get_tool(self, tenant_id: str, tool_id: str) -> ToolRecord | None:
        """Fetch a tool by id for a tenant."""
        raise NotImplementedError

    async def list_tools(self, tenant_id: str) -> list[ToolRecord]:
        """List all tools for a tenant."""
        raise NotImplementedError

    async def save_tool(self, record: ToolRecord) -> None:
        """Persist a tool record."""
        raise NotImplementedError

    async def get_data_source(
        self, tenant_id: str, data_source_id: str
    ) -> DataSourceRecord | None:
        """Fetch a data source by id for a tenant."""
        raise NotImplementedError

    async def list_data_sources(self, tenant_id: str) -> list[DataSourceRecord]:
        """List all data sources for a tenant."""
        raise NotImplementedError

    async def save_data_source(self, record: DataSourceRecord) -> None:
        """Persist a data source record."""
        raise NotImplementedError
