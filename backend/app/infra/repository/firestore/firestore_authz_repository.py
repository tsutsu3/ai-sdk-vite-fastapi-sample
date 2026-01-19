from logging import getLogger

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

logger = getLogger(__name__)


class FirestoreAuthzRepository(AuthzRepository):
    def __init__(
        self,
        *,
        tenants_collection,
        users_collection,
        identities_collection,
        memberships_collection,
    ) -> None:
        self._tenants = tenants_collection
        self._users = users_collection
        self._user_identities = identities_collection
        self._memberships = memberships_collection

    def __str__(self) -> str:
        return (
            "FirestoreAuthzRepository("
            f"tenants={self._tenants._path}, "
            f"users={self._users._path}, "
            f"identities={self._user_identities._path}, "
            f"memberships={self._memberships._path}"
            ")"
        )

    async def get_user(self, user_id: str) -> UserRecord | None:
        logger.debug("firestore.authz.get_user id=%s", user_id)
        doc = await self._users.document(user_id).get()
        if not doc.exists:
            return None
        try:
            return user_doc_to_record(UserDoc.model_validate(doc.to_dict()))
        except Exception:
            return None

    async def get_tenant(self, tenant_id: str) -> TenantRecord | None:
        logger.debug("firestore.authz.get_tenant id=%s", tenant_id)
        doc = await self._tenants.document(tenant_id).get()
        if not doc.exists:
            return None
        try:
            return tenant_doc_to_record(TenantDoc.model_validate(doc.to_dict()))
        except Exception:
            return None

    async def get_user_identity(self, identity_id: str) -> UserIdentityRecord | None:
        logger.debug("firestore.authz.get_identity id=%s", identity_id)
        doc = await self._user_identities.document(identity_id).get()
        if not doc.exists:
            return None
        try:
            return user_identity_doc_to_record(UserIdentityDoc.model_validate(doc.to_dict()))
        except Exception:
            return None

    async def list_memberships_by_email(
        self, email: str, status: MembershipStatus
    ) -> list[MembershipRecord]:
        logger.debug("firestore.authz.list_memberships status=%s", status.value)
        query = self._memberships.where("invite_email", "==", email).where(
            "status", "==", status.value
        )
        results: list[MembershipRecord] = []
        async for doc in query.stream():
            try:
                results.append(
                    membership_doc_to_record(MembershipDoc.model_validate(doc.to_dict()))
                )
            except Exception:
                continue
        return results

    async def list_memberships_by_user(self, user_id: str) -> list[MembershipRecord]:
        logger.debug("firestore.authz.list_memberships_by_user user_id=%s", user_id)
        query = self._memberships.where("user_id", "==", user_id)
        results: list[MembershipRecord] = []
        async for doc in query.stream():
            try:
                results.append(
                    membership_doc_to_record(MembershipDoc.model_validate(doc.to_dict()))
                )
            except Exception:
                continue
        return results

    async def get_membership_for_user(
        self, tenant_id: str, user_id: str
    ) -> MembershipRecord | None:
        logger.debug("firestore.authz.get_membership tenant_id=%s user_id=%s", tenant_id, user_id)
        query = self._memberships.where("tenant_id", "==", tenant_id).where(
            "user_id", "==", user_id
        )
        async for doc in query.stream():
            try:
                return membership_doc_to_record(MembershipDoc.model_validate(doc.to_dict()))
            except Exception:
                return None
        return None

    async def save_user(self, record: UserRecord) -> None:
        if not record.id:
            raise ValueError("UserRecord.id is required for persistence")
        doc = user_record_to_doc(record)
        await self._users.document(record.id).set(
            doc.model_dump(by_alias=True, exclude_none=True)
        )

    async def save_user_identity(self, record: UserIdentityRecord) -> None:
        doc = user_identity_record_to_doc(record)
        await self._user_identities.document(record.id).set(
            doc.model_dump(by_alias=True, exclude_none=True)
        )

    async def save_membership(self, record: MembershipRecord) -> None:
        doc = membership_record_to_doc(record)
        await self._memberships.document(record.id).set(
            doc.model_dump(by_alias=True, exclude_none=True)
        )

    async def save_tenant(self, record: TenantRecord) -> None:
        doc = tenant_record_to_doc(record)
        await self._tenants.document(record.id).set(
            doc.model_dump(by_alias=True, exclude_none=True)
        )
