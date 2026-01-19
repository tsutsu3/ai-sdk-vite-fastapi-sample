import asyncio
import random

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


class MemoryAuthzRepository(AuthzRepository):
    def __init__(
        self,
        tenants: dict[str, TenantRecord] | None = None,
        users: dict[str, UserRecord] | None = None,
        user_identities: dict[str, UserIdentityRecord] | None = None,
        memberships: dict[str, MembershipRecord] | None = None,
        delay_max_seconds: float = 2.0,
    ) -> None:
        self._tenants: dict[str, TenantDoc] = {}
        self._users: dict[str, UserDoc] = {}
        self._user_identities: dict[str, UserIdentityDoc] = {}
        self._memberships: dict[str, MembershipDoc] = {}
        self._delay_max_seconds = max(delay_max_seconds, 0.0)
        if tenants:
            self._tenants = {
                tenant_id: tenant_record_to_doc(record) for tenant_id, record in tenants.items()
            }
        if users:
            self._users = {
                user_id: user_record_to_doc(record) for user_id, record in users.items()
            }
        if user_identities:
            self._user_identities = {
                identity_id: user_identity_record_to_doc(record)
                for identity_id, record in user_identities.items()
            }
        if memberships:
            self._memberships = {
                membership_id: membership_record_to_doc(record)
                for membership_id, record in memberships.items()
            }

    async def _sleep(self) -> None:
        if self._delay_max_seconds <= 0:
            return
        await asyncio.sleep(random.random() * self._delay_max_seconds)

    async def get_user(self, user_id: str) -> UserRecord | None:
        await self._sleep()
        doc = self._users.get(user_id)
        return user_doc_to_record(doc) if doc else None

    async def get_tenant(self, tenant_id: str) -> TenantRecord | None:
        await self._sleep()
        doc = self._tenants.get(tenant_id)
        return tenant_doc_to_record(doc) if doc else None

    async def get_user_identity(self, identity_id: str) -> UserIdentityRecord | None:
        await self._sleep()
        doc = self._user_identities.get(identity_id)
        return user_identity_doc_to_record(doc) if doc else None

    async def list_memberships_by_email(
        self, email: str, status: MembershipStatus
    ) -> list[MembershipRecord]:
        await self._sleep()
        return [
            membership_doc_to_record(doc)
            for doc in self._memberships.values()
            if doc.invite_email == email and doc.status == status
        ]

    async def list_memberships_by_user(self, user_id: str) -> list[MembershipRecord]:
        await self._sleep()
        return [
            membership_doc_to_record(doc)
            for doc in self._memberships.values()
            if doc.user_id == user_id
        ]

    async def get_membership_for_user(
        self, tenant_id: str, user_id: str
    ) -> MembershipRecord | None:
        await self._sleep()
        for doc in self._memberships.values():
            if doc.tenant_id == tenant_id and doc.user_id == user_id:
                return membership_doc_to_record(doc)
        return None

    async def save_user(self, record: UserRecord) -> None:
        await self._sleep()
        if not record.id:
            raise ValueError("UserRecord.id is required for persistence")
        self._users[record.id] = user_record_to_doc(record)

    async def save_user_identity(self, record: UserIdentityRecord) -> None:
        await self._sleep()
        self._user_identities[record.id] = user_identity_record_to_doc(record)

    async def save_membership(self, record: MembershipRecord) -> None:
        await self._sleep()
        self._memberships[record.id] = membership_record_to_doc(record)

    async def save_tenant(self, record: TenantRecord) -> None:
        await self._sleep()
        from app.infra.mapper.authz_mapper import tenant_record_to_doc

        self._tenants[record.id] = tenant_record_to_doc(record)
