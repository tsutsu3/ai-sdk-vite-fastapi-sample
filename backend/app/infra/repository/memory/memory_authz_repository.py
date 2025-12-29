import asyncio
import random

from app.features.authz.models import (
    ProvisioningRecord,
    ProvisioningStatus,
    TenantRecord,
    UserIdentityRecord,
    UserRecord,
)
from app.features.authz.ports import AuthzRepository
from app.infra.mapper.authz_mapper import (
    provisioning_doc_to_record,
    provisioning_record_to_doc,
    tenant_doc_to_record,
    tenant_record_to_doc,
    user_doc_to_record,
    user_identity_doc_to_record,
    user_identity_record_to_doc,
    user_record_to_doc,
)
from app.infra.model.authz_model import (
    ProvisioningDoc,
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
        provisioning: dict[str, ProvisioningRecord] | None = None,
    ) -> None:
        self._tenants: dict[str, TenantDoc] = {}
        self._users: dict[str, UserDoc] = {}
        self._user_identities: dict[str, UserIdentityDoc] = {}
        self._provisioning: dict[str, ProvisioningDoc] = {}
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
        if provisioning:
            self._provisioning = {
                provisioning_id: provisioning_record_to_doc(record)
                for provisioning_id, record in provisioning.items()
            }

    async def get_user(self, user_id: str) -> UserRecord | None:
        await asyncio.sleep(random.random() * 2)
        doc = self._users.get(user_id)
        return user_doc_to_record(doc) if doc else None

    async def get_tenant(self, tenant_id: str) -> TenantRecord | None:
        await asyncio.sleep(random.random() * 2)
        doc = self._tenants.get(tenant_id)
        return tenant_doc_to_record(doc) if doc else None

    async def get_user_identity(self, identity_id: str) -> UserIdentityRecord | None:
        await asyncio.sleep(random.random() * 2)
        doc = self._user_identities.get(identity_id)
        return user_identity_doc_to_record(doc) if doc else None

    async def list_provisioning_by_email(
        self, email: str, status: ProvisioningStatus
    ) -> list[ProvisioningRecord]:
        await asyncio.sleep(random.random() * 2)
        return [
            provisioning_doc_to_record(doc)
            for doc in self._provisioning.values()
            if doc.email == email and doc.status == status
        ]

    async def save_user(self, record: UserRecord) -> None:
        await asyncio.sleep(random.random() * 2)
        if not record.id:
            raise ValueError("UserRecord.id is required for persistence")
        self._users[record.id] = user_record_to_doc(record)

    async def save_user_identity(self, record: UserIdentityRecord) -> None:
        await asyncio.sleep(random.random() * 2)
        self._user_identities[record.id] = user_identity_record_to_doc(record)

    async def save_provisioning(self, record: ProvisioningRecord) -> None:
        await asyncio.sleep(random.random() * 2)
        self._provisioning[record.id] = provisioning_record_to_doc(record)
