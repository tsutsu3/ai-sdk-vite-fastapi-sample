from pathlib import Path

from app.features.tool_catalog.models import DataSourceRecord, ToolRecord
from app.features.tool_catalog.ports import ToolCatalogRepository
from app.infra.mapper.tool_catalog_mapper import (
    data_source_doc_to_record,
    data_source_record_to_doc,
    tool_doc_to_record,
    tool_record_to_doc,
)
from app.infra.model.tool_catalog_model import DataSourceDoc, ToolDoc


class LocalToolCatalogRepository(ToolCatalogRepository):
    """Local file-backed tool catalog repository."""

    def __init__(
        self,
        base_path: Path,
        *,
        tools: dict[str, dict[str, ToolRecord]] | None = None,
        data_sources: dict[str, dict[str, DataSourceRecord]] | None = None,
    ) -> None:
        self._base_path = base_path
        if tools:
            for tenant_id, tenant_tools in tools.items():
                for tool_id, tool in tenant_tools.items():
                    self._write_tool(tenant_id, tool_id, tool)
        if data_sources:
            for tenant_id, tenant_sources in data_sources.items():
                for source_id, source in tenant_sources.items():
                    self._write_data_source(tenant_id, source_id, source)

    async def get_tool(self, tenant_id: str, tool_id: str) -> ToolRecord | None:
        path = self._tool_dir(tenant_id) / f"{tool_id}.json"
        if not path.exists():
            return None
        try:
            content = path.read_text(encoding="utf-8")
            doc = ToolDoc.model_validate_json(content)
        except Exception:
            return None
        return tool_doc_to_record(doc)

    async def list_tools(self, tenant_id: str) -> list[ToolRecord]:
        tools: list[ToolRecord] = []
        tool_dir = self._tool_dir(tenant_id)
        if not tool_dir.exists():
            return tools
        for path in tool_dir.glob("*.json"):
            try:
                content = path.read_text(encoding="utf-8")
                doc = ToolDoc.model_validate_json(content)
            except Exception:
                continue
            tools.append(tool_doc_to_record(doc))
        return tools

    async def save_tool(self, record: ToolRecord) -> None:
        self._write_tool(record.tenant_id, record.id, record)

    async def get_data_source(
        self, tenant_id: str, data_source_id: str
    ) -> DataSourceRecord | None:
        path = self._data_source_dir(tenant_id) / f"{data_source_id}.json"
        if not path.exists():
            return None
        try:
            content = path.read_text(encoding="utf-8")
            doc = DataSourceDoc.model_validate_json(content)
        except Exception:
            return None
        return data_source_doc_to_record(doc)

    async def list_data_sources(self, tenant_id: str) -> list[DataSourceRecord]:
        sources: list[DataSourceRecord] = []
        source_dir = self._data_source_dir(tenant_id)
        if not source_dir.exists():
            return sources
        for path in source_dir.glob("*.json"):
            try:
                content = path.read_text(encoding="utf-8")
                doc = DataSourceDoc.model_validate_json(content)
            except Exception:
                continue
            sources.append(data_source_doc_to_record(doc))
        return sources

    async def save_data_source(self, record: DataSourceRecord) -> None:
        self._write_data_source(record.tenant_id, record.id, record)

    def _catalog_dir(self) -> Path:
        return self._base_path / "tool-catalog"

    def _tenant_dir(self, tenant_id: str) -> Path:
        return self._catalog_dir() / tenant_id

    def _tool_dir(self, tenant_id: str) -> Path:
        return self._tenant_dir(tenant_id) / "tools"

    def _data_source_dir(self, tenant_id: str) -> Path:
        return self._tenant_dir(tenant_id) / "data-sources"

    def _write_tool(self, tenant_id: str, tool_id: str, record: ToolRecord) -> None:
        tool_dir = self._tool_dir(tenant_id)
        tool_dir.mkdir(parents=True, exist_ok=True)
        path = tool_dir / f"{tool_id}.json"
        doc = tool_record_to_doc(record)
        path.write_text(doc.model_dump_json(ensure_ascii=False), encoding="utf-8")

    def _write_data_source(
        self, tenant_id: str, data_source_id: str, record: DataSourceRecord
    ) -> None:
        source_dir = self._data_source_dir(tenant_id)
        source_dir.mkdir(parents=True, exist_ok=True)
        path = source_dir / f"{data_source_id}.json"
        doc = data_source_record_to_doc(record)
        path.write_text(doc.model_dump_json(ensure_ascii=False), encoding="utf-8")
