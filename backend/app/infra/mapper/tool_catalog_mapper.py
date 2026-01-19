from datetime import datetime

from app.features.tool_catalog.models import DataSourceRecord, ToolPrompts, ToolRecord
from app.infra.model.tool_catalog_model import (
    DataSourceDoc,
    ToolDoc,
    ToolPromptsDoc,
)


def _ensure_datetime(value: datetime | str | None) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value
    try:
        normalized = value.replace("Z", "+00:00") if value.endswith("Z") else value
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def _format_datetime(value: datetime | None) -> str:
    return value.isoformat() if value else ""


def tool_prompts_doc_to_record(doc: ToolPromptsDoc) -> ToolPrompts:
    return ToolPrompts(
        system=doc.system,
        query=doc.query,
        hyde=doc.hyde,
        follow_up=doc.follow_up,
        template=doc.template,
        chapter=doc.chapter,
        merge=doc.merge,
        proofread=doc.proofread,
    )


def tool_prompts_record_to_doc(record: ToolPrompts) -> ToolPromptsDoc:
    return ToolPromptsDoc(
        system=record.system,
        query=record.query,
        hyde=record.hyde,
        follow_up=record.follow_up,
        template=record.template,
        chapter=record.chapter,
        merge=record.merge,
        proofread=record.proofread,
    )


def tool_doc_to_record(doc: ToolDoc) -> ToolRecord:
    return ToolRecord(
        id=doc.id,
        tenant_id=doc.tenant_id,
        group_id=doc.group_id,
        group_label_key=doc.group_label_key,
        group_order=doc.group_order,
        label_key=doc.label_key,
        description_key=doc.description_key,
        data_source_id=doc.data_source_id,
        mode=doc.mode,
        top_k=doc.top_k,
        enabled=doc.enabled,
        get_extractive_answers=doc.get_extractive_answers,
        prompts=tool_prompts_doc_to_record(doc.prompts),
        created_at=_ensure_datetime(doc.created_at),
        updated_at=_ensure_datetime(doc.updated_at),
    )


def tool_record_to_doc(record: ToolRecord) -> ToolDoc:
    return ToolDoc(
        id=record.id,
        tenant_id=record.tenant_id,
        group_id=record.group_id,
        group_label_key=record.group_label_key,
        group_order=record.group_order,
        label_key=record.label_key,
        description_key=record.description_key,
        data_source_id=record.data_source_id,
        mode=record.mode,
        top_k=record.top_k,
        enabled=record.enabled,
        get_extractive_answers=record.get_extractive_answers,
        prompts=tool_prompts_record_to_doc(record.prompts),
        created_at=_format_datetime(record.created_at),
        updated_at=_format_datetime(record.updated_at),
    )


def data_source_doc_to_record(doc: DataSourceDoc) -> DataSourceRecord:
    return DataSourceRecord(
        id=doc.id,
        tenant_id=doc.tenant_id,
        provider=doc.provider,
        data_source=doc.data_source,
        config=dict(doc.config),
        enabled=doc.enabled,
        created_at=_ensure_datetime(doc.created_at),
        updated_at=_ensure_datetime(doc.updated_at),
    )


def data_source_record_to_doc(record: DataSourceRecord) -> DataSourceDoc:
    return DataSourceDoc(
        id=record.id,
        tenant_id=record.tenant_id,
        provider=record.provider,
        data_source=record.data_source,
        config=dict(record.config),
        enabled=record.enabled,
        created_at=_format_datetime(record.created_at),
        updated_at=_format_datetime(record.updated_at),
    )
