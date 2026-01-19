from datetime import datetime

from app.features.authz.models import (
    MembershipRecord,
    TenantRecord,
    ToolOverridesRecord,
    UserIdentityRecord,
    UserRecord,
)
from app.infra.model.authz_model import (
    MembershipDoc,
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
        default_tool_ids=list(doc.default_tool_ids),
        created_at=_ensure_datetime(doc.created_at),
        updated_at=_ensure_datetime(doc.updated_at),
    )


def tenant_record_to_doc(record: TenantRecord) -> TenantDoc:
    return TenantDoc(
        id=record.id,
        key=record.key or record.id,
        name=record.name,
        default_tool_ids=list(record.default_tool_ids),
        created_at=_format_datetime(record.created_at),
        updated_at=_format_datetime(record.updated_at),
    )


def user_doc_to_record(doc: UserDoc) -> UserRecord:
    return UserRecord(
        id=doc.id,
        active_tenant_id=doc.active_tenant_id or "",
        email=doc.email,
        first_name=doc.first_name,
        last_name=doc.last_name,
        created_at=_ensure_datetime(doc.created_at),
        updated_at=_ensure_datetime(doc.updated_at),
    )


def user_record_to_doc(record: UserRecord) -> UserDoc:
    return UserDoc(
        id=record.id or "",
        active_tenant_id=record.active_tenant_id,
        email=record.email or "",
        first_name=record.first_name or "",
        last_name=record.last_name or "",
        created_at=_format_datetime(record.created_at),
        updated_at=_format_datetime(record.updated_at),
    )


def user_identity_doc_to_record(doc: UserIdentityDoc) -> UserIdentityRecord:
    return UserIdentityRecord(
        id=doc.id,
        provider=doc.provider,
        user_id=doc.user_id,
        created_at=_ensure_datetime(doc.created_at),
        updated_at=_ensure_datetime(doc.updated_at),
    )


def user_identity_record_to_doc(record: UserIdentityRecord) -> UserIdentityDoc:
    return UserIdentityDoc(
        id=record.id,
        provider=record.provider or "",
        user_id=record.user_id,
        created_at=_format_datetime(record.created_at),
        updated_at=_format_datetime(record.updated_at),
    )


def membership_doc_to_record(doc: MembershipDoc) -> MembershipRecord:
    return MembershipRecord(
        id=doc.id,
        tenant_id=doc.tenant_id,
        user_id=doc.user_id,
        invite_email=doc.invite_email,
        role=doc.role,
        tool_overrides=tool_overrides_doc_to_record(doc.tool_overrides),
        status=doc.status,
        created_at=_ensure_datetime(doc.created_at),
        updated_at=_ensure_datetime(doc.updated_at),
    )


def membership_record_to_doc(record: MembershipRecord) -> MembershipDoc:
    return MembershipDoc(
        id=record.id,
        tenant_id=record.tenant_id,
        user_id=record.user_id,
        invite_email=record.invite_email,
        role=record.role,
        tool_overrides=tool_overrides_record_to_doc(record.tool_overrides),
        status=record.status,
        created_at=_format_datetime(record.created_at),
        updated_at=_format_datetime(record.updated_at),
    )
