from datetime import datetime

from app.features.authz.models import (
    ProvisioningRecord,
    TenantRecord,
    ToolOverridesRecord,
    UserIdentityRecord,
    UserRecord,
)
from app.infra.model.authz_model import (
    ProvisioningDoc,
    TenantDoc,
    ToolOverridesDoc,
    UserDoc,
    UserIdentityDoc,
)


def tool_overrides_doc_to_record(doc: ToolOverridesDoc) -> ToolOverridesRecord:
    return ToolOverridesRecord(
        allow=list(doc.allow),
        deny=list(doc.deny),
    )


def tool_overrides_record_to_doc(record: ToolOverridesRecord) -> ToolOverridesDoc:
    return ToolOverridesDoc(
        allow=list(record.allow),
        deny=list(record.deny),
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


def tenant_doc_to_record(doc: TenantDoc) -> TenantRecord:
    return TenantRecord(
        id=doc.id,
        key=doc.key,
        name=doc.name,
        default_tools=list(doc.default_tools),
        created_at=_ensure_datetime(doc.created_at),
        updated_at=_ensure_datetime(doc.updated_at),
    )


def tenant_record_to_doc(record: TenantRecord) -> TenantDoc:
    return TenantDoc(
        id=record.id,
        key=record.key or record.id,
        name=record.name,
        default_tools=list(record.default_tools),
        created_at=_format_datetime(record.created_at),
        updated_at=_format_datetime(record.updated_at),
    )


def user_doc_to_record(doc: UserDoc) -> UserRecord:
    tenant_ids = list(doc.tenant_ids)
    if not tenant_ids and doc.tenant_id:
        tenant_ids = [doc.tenant_id]
    active_tenant_id = doc.active_tenant_id or (tenant_ids[0] if tenant_ids else "")
    overrides_by_tenant: dict[str, ToolOverridesRecord] = {}
    if doc.tool_overrides_by_tenant:
        for tenant_id, overrides in doc.tool_overrides_by_tenant.items():
            overrides_by_tenant[tenant_id] = tool_overrides_doc_to_record(overrides)
    elif doc.tool_overrides and active_tenant_id:
        overrides_by_tenant[active_tenant_id] = tool_overrides_doc_to_record(
            doc.tool_overrides
        )
    return UserRecord(
        id=doc.id,
        tenant_ids=tenant_ids,
        active_tenant_id=active_tenant_id,
        email=doc.email,
        first_name=doc.first_name,
        last_name=doc.last_name,
        tool_overrides_by_tenant=overrides_by_tenant,
        created_at=_ensure_datetime(doc.created_at),
        updated_at=_ensure_datetime(doc.updated_at),
    )


def user_record_to_doc(record: UserRecord) -> UserDoc:
    overrides_by_tenant: dict[str, ToolOverridesDoc] = {
        tenant_id: tool_overrides_record_to_doc(overrides)
        for tenant_id, overrides in record.tool_overrides_by_tenant.items()
    }
    return UserDoc(
        id=record.id or "",
        # idp_id=record.idp_id or "",
        tenant_ids=list(record.tenant_ids),
        active_tenant_id=record.active_tenant_id,
        email=record.email or "",
        first_name=record.first_name or "",
        last_name=record.last_name or "",
        tool_overrides_by_tenant=overrides_by_tenant,
        created_at=_format_datetime(record.created_at),
        updated_at=_format_datetime(record.updated_at),
    )


def user_identity_doc_to_record(doc: UserIdentityDoc) -> UserIdentityRecord:
    return UserIdentityRecord(
        id=doc.id,
        provider=doc.provider,
        user_id=doc.user_id,
        tenant_id=doc.tenant_id,
        created_at=_ensure_datetime(doc.created_at),
        updated_at=_ensure_datetime(doc.updated_at),
    )


def user_identity_record_to_doc(record: UserIdentityRecord) -> UserIdentityDoc:
    return UserIdentityDoc(
        id=record.id,
        provider=record.provider or "",
        user_id=record.user_id,
        tenant_id=record.tenant_id,
        created_at=_format_datetime(record.created_at),
        updated_at=_format_datetime(record.updated_at),
    )


def provisioning_doc_to_record(doc: ProvisioningDoc) -> ProvisioningRecord:
    return ProvisioningRecord(
        id=doc.id,
        email=doc.email,
        tenant_id=doc.tenant_id,
        first_name=doc.first_name,
        last_name=doc.last_name,
        tool_overrides=tool_overrides_doc_to_record(doc.tool_overrides),
        status=doc.status,
        created_at=_ensure_datetime(doc.created_at),
        updated_at=_ensure_datetime(doc.updated_at),
    )


def provisioning_record_to_doc(record: ProvisioningRecord) -> ProvisioningDoc:
    return ProvisioningDoc(
        id=record.id,
        email=record.email,
        tenant_id=record.tenant_id,
        first_name=record.first_name,
        last_name=record.last_name,
        tool_overrides=tool_overrides_record_to_doc(record.tool_overrides),
        status=record.status,
        created_at=_format_datetime(record.created_at),
        updated_at=_format_datetime(record.updated_at),
    )
