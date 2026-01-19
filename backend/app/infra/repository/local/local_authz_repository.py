from pathlib import Path

from app.features.authz.models import (
    MembershipRecord,
    MembershipStatus,
    TenantRecord,
    UserIdentityRecord,
    UserRecord,
)
from app.features.authz.ports import AuthzRepository
from app.infra.mapper.authz_mapper import (
    membership_doc_to_record,
    membership_record_to_doc,
    tenant_doc_to_record,
    tenant_record_to_doc,
    user_doc_to_record,
    user_identity_doc_to_record,
    user_identity_record_to_doc,
    user_record_to_doc,
)
from app.infra.model.authz_model import (
    MembershipDoc,
    TenantDoc,
    UserDoc,
    UserIdentityDoc,
)


class LocalAuthzRepository(AuthzRepository):
    def __init__(
        self,
        base_path: Path,
        tenants: dict[str, TenantRecord] | None = None,
        users: dict[str, UserRecord] | None = None,
        user_identities: dict[str, UserIdentityRecord] | None = None,
        memberships: dict[str, MembershipRecord] | None = None,
    ) -> None:
        self._base_path = base_path
        if tenants and not self._tenant_dir().exists():
            for tenant_id, tenant in tenants.items():
                self._write_tenant(tenant_id, tenant)
        if users and not self._user_dir().exists():
            for user_id, user in users.items():
                self._write_user(user_id, user)
        if user_identities and not self._user_identity_dir().exists():
            for identity_id, identity in user_identities.items():
                self._write_user_identity(identity_id, identity)
        if memberships and not self._membership_dir().exists():
            for membership_id, record in memberships.items():
                self._write_membership(membership_id, record)

    async def get_user(self, user_id: str) -> UserRecord | None:
        return self._read_user_item(user_id)

    async def get_tenant(self, tenant_id: str) -> TenantRecord | None:
        return self._read_tenant_item(tenant_id)

    async def get_user_identity(self, identity_id: str) -> UserIdentityRecord | None:
        return self._read_user_identity_item(identity_id)

    async def list_memberships_by_email(
        self, email: str, status: MembershipStatus
    ) -> list[MembershipRecord]:
        return [
            record
            for record in self._read_all_memberships()
            if record.invite_email == email and record.status == status
        ]

    async def list_memberships_by_user(self, user_id: str) -> list[MembershipRecord]:
        return [record for record in self._read_all_memberships() if record.user_id == user_id]

    async def get_membership_for_user(
        self, tenant_id: str, user_id: str
    ) -> MembershipRecord | None:
        for record in self._read_all_memberships():
            if record.tenant_id == tenant_id and record.user_id == user_id:
                return record
        return None

    async def save_user(self, record: UserRecord) -> None:
        if not record.id:
            raise ValueError("UserRecord.id is required for persistence")
        self._write_user(record.id, record)

    async def save_user_identity(self, record: UserIdentityRecord) -> None:
        self._write_user_identity(record.id, record)

    async def save_membership(self, record: MembershipRecord) -> None:
        self._write_membership(record.id, record)

    async def save_tenant(self, record: TenantRecord) -> None:
        self._write_tenant(record.id, record)

    def _tenant_dir(self) -> Path:
        return self._base_path / "tenants"

    def _user_dir(self) -> Path:
        return self._base_path / "users"

    def _user_identity_dir(self) -> Path:
        return self._base_path / "useridentities"

    def _membership_dir(self) -> Path:
        return self._base_path / "memberships"

    def _write_tenant(self, tenant_id: str, tenant_record: TenantRecord) -> None:
        tenant_dir = self._tenant_dir()
        tenant_dir.mkdir(parents=True, exist_ok=True)
        tenant_path = tenant_dir / f"{tenant_id}.json"
        doc = tenant_record_to_doc(tenant_record)
        tenant_path.write_text(doc.model_dump_json(ensure_ascii=False), encoding="utf-8")

    def _write_user(self, user_id: str, user_record: UserRecord) -> None:
        user_dir = self._user_dir()
        user_dir.mkdir(parents=True, exist_ok=True)
        user_path = user_dir / f"{user_id}.json"
        doc = user_record_to_doc(user_record)
        user_path.write_text(doc.model_dump_json(ensure_ascii=False), encoding="utf-8")

    def _write_user_identity(self, identity_id: str, identity_record: UserIdentityRecord) -> None:
        identity_dir = self._user_identity_dir()
        identity_dir.mkdir(parents=True, exist_ok=True)
        identity_path = identity_dir / f"{identity_id}.json"
        doc = user_identity_record_to_doc(identity_record)
        identity_path.write_text(doc.model_dump_json(ensure_ascii=False), encoding="utf-8")

    def _write_membership(self, membership_id: str, membership_record: MembershipRecord) -> None:
        membership_dir = self._membership_dir()
        membership_dir.mkdir(parents=True, exist_ok=True)
        membership_path = membership_dir / f"{membership_id}.json"
        doc = membership_record_to_doc(membership_record)
        membership_path.write_text(doc.model_dump_json(ensure_ascii=False), encoding="utf-8")

    def _read_user_item(self, user_id: str) -> UserRecord | None:
        user_path = self._user_dir() / f"{user_id}.json"
        if not user_path.exists():
            return None
        try:
            content = user_path.read_text(encoding="utf-8")
            doc = UserDoc.model_validate_json(content)
        except Exception:
            return None
        return user_doc_to_record(doc)

    def _read_tenant_item(self, tenant_id: str) -> TenantRecord | None:
        tenant_path = self._tenant_dir() / f"{tenant_id}.json"
        if not tenant_path.exists():
            return None
        try:
            content = tenant_path.read_text(encoding="utf-8")
            doc = TenantDoc.model_validate_json(content)
        except Exception:
            return None
        return tenant_doc_to_record(doc)

    def _read_user_identity_item(self, identity_id: str) -> UserIdentityRecord | None:
        identity_path = self._user_identity_dir() / f"{identity_id}.json"
        if not identity_path.exists():
            return None
        try:
            content = identity_path.read_text(encoding="utf-8")
            doc = UserIdentityDoc.model_validate_json(content)
        except Exception:
            return None
        return user_identity_doc_to_record(doc)

    def _read_all_memberships(self) -> list[MembershipRecord]:
        membership_dir = self._membership_dir()
        if not membership_dir.exists():
            return []

        records: list[MembershipRecord] = []
        for path in membership_dir.glob("*.json"):
            try:
                content = path.read_text(encoding="utf-8")
                doc = MembershipDoc.model_validate_json(content)
            except Exception:
                continue
            records.append(membership_doc_to_record(doc))
        return records
