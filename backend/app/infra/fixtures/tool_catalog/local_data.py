from app.features.retrieval.tools.registry import ProviderEnum, RetrievalToolModeEnum
from app.features.tool_catalog.models import DataSourceRecord, ToolPrompts, ToolRecord
from app.shared.time import now_datetime

_BASE_TOOLS: list[ToolRecord] = [
    ToolRecord(
        id="tool0101",
        tenant_id="",
        group_id="tool01",
        group_label_key="tool01",
        group_order=10,
        label_key="tool0101",
        description_key="homeToolDescription.tool0101",
        data_source_id="tool0101",
        mode=RetrievalToolModeEnum.SIMPLE,
        top_k=5,
        prompts=ToolPrompts(system="You answer questions using provided sources."),
        created_at=now_datetime(),
        updated_at=now_datetime(),
    ),
    ToolRecord(
        id="tool0102",
        tenant_id="",
        group_id="tool01",
        group_label_key="tool01",
        group_order=10,
        label_key="tool0102",
        description_key="homeToolDescription.tool0102",
        data_source_id="tool0102",
        mode=RetrievalToolModeEnum.CHAT,
        top_k=5,
        prompts=ToolPrompts(system="You answer questions using provided sources."),
        created_at=now_datetime(),
        updated_at=now_datetime(),
    ),
    ToolRecord(
        id="tool0201",
        tenant_id="",
        group_id="tool02",
        group_label_key="tool02",
        group_order=20,
        label_key="tool0201",
        description_key="homeToolDescription.tool0201",
        data_source_id="tool0201",
        mode=RetrievalToolModeEnum.SIMPLE,
        top_k=5,
        prompts=ToolPrompts(system="You answer questions using provided sources."),
        created_at=now_datetime(),
        updated_at=now_datetime(),
    ),
    ToolRecord(
        id="tool0202",
        tenant_id="",
        group_id="tool02",
        group_label_key="tool02",
        group_order=20,
        label_key="tool0202",
        description_key="homeToolDescription.tool0202",
        data_source_id="tool0202",
        mode=RetrievalToolModeEnum.CHAT,
        top_k=5,
        prompts=ToolPrompts(system="You answer questions using provided sources."),
        created_at=now_datetime(),
        updated_at=now_datetime(),
    ),
    ToolRecord(
        id="tool0301",
        tenant_id="",
        group_id="tool03",
        group_label_key="tool03",
        group_order=30,
        label_key="tool0301",
        description_key="homeToolDescription.tool0301",
        data_source_id="tool0301",
        mode=RetrievalToolModeEnum.SIMPLE,
        top_k=5,
        prompts=ToolPrompts(system="You answer questions using provided sources."),
        created_at=now_datetime(),
        updated_at=now_datetime(),
    ),
    ToolRecord(
        id="tool0302",
        tenant_id="",
        group_id="tool03",
        group_label_key="tool03",
        group_order=30,
        label_key="tool0302",
        description_key="homeToolDescription.tool0302",
        data_source_id="tool0302",
        mode=RetrievalToolModeEnum.CHAT,
        top_k=5,
        prompts=ToolPrompts(system="You answer questions using provided sources."),
        created_at=now_datetime(),
        updated_at=now_datetime(),
    ),
]

_BASE_DATA_SOURCES: list[DataSourceRecord] = [
    DataSourceRecord(
        id="tool0101",
        tenant_id="",
        provider=ProviderEnum.LOCAL_FILES,
        data_source="tool0101",
        created_at=now_datetime(),
        updated_at=now_datetime(),
    ),
    DataSourceRecord(
        id="tool0102",
        tenant_id="",
        provider=ProviderEnum.LOCAL_FILES,
        data_source="tool0102",
        created_at=now_datetime(),
        updated_at=now_datetime(),
    ),
    DataSourceRecord(
        id="tool0201",
        tenant_id="",
        provider=ProviderEnum.LOCAL_FILES,
        data_source="tool0201",
        created_at=now_datetime(),
        updated_at=now_datetime(),
    ),
    DataSourceRecord(
        id="tool0202",
        tenant_id="",
        provider=ProviderEnum.LOCAL_FILES,
        data_source="tool0202",
        created_at=now_datetime(),
        updated_at=now_datetime(),
    ),
    DataSourceRecord(
        id="tool0301",
        tenant_id="",
        provider=ProviderEnum.LOCAL_FILES,
        data_source="tool0301",
        created_at=now_datetime(),
        updated_at=now_datetime(),
    ),
    DataSourceRecord(
        id="tool0302",
        tenant_id="",
        provider=ProviderEnum.LOCAL_FILES,
        data_source="tool0302",
        created_at=now_datetime(),
        updated_at=now_datetime(),
    ),
]


def build_tools_for_tenant(tenant_id: str) -> dict[str, ToolRecord]:
    return {
        tool.id: tool.model_copy(update={"tenant_id": tenant_id})
        for tool in _BASE_TOOLS
    }


def build_data_sources_for_tenant(tenant_id: str) -> dict[str, DataSourceRecord]:
    return {
        source.id: source.model_copy(update={"tenant_id": tenant_id})
        for source in _BASE_DATA_SOURCES
    }
