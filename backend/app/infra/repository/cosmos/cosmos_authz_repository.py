from azure.cosmos.aio import ContainerProxy

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


def user_partition(user_id: str) -> str:
    """Return the Cosmos DB partition key for user items.

    Args:
        user_id: User identifier.

    Returns:
        str: Partition key value.
    """
    return user_id


class CosmosAuthzRepository(AuthzRepository):
    def __init__(
        self,
        *,
        users_container: ContainerProxy,
        tenants_container: ContainerProxy,
        identities_container: ContainerProxy,
        memberships_container: ContainerProxy,
    ) -> None:
        self._users_container = users_container
        self._tenants_container = tenants_container
        self._identities_container = identities_container
        self._memberships_container = memberships_container

    async def get_user(self, user_id: str) -> UserRecord | None:
        return await self._read_user_item(user_id)

    async def get_tenant(self, tenant_id: str) -> TenantRecord | None:
        return await self._read_tenant_item(tenant_id)

    async def get_user_identity(self, identity_id: str) -> UserIdentityRecord | None:
        return await self._read_user_identity_item(identity_id)

    async def list_memberships_by_email(
        self, email: str, status: MembershipStatus
    ) -> list[MembershipRecord]:
        items = self._memberships_container.query_items(
            query=(
                "SELECT * FROM c WHERE c.invite_email = @email AND c.status = @status"
            ),
            parameters=[
                {"name": "@email", "value": email},
                {"name": "@status", "value": status.value},
            ],
            partition_key=email,
        )
        records: list[MembershipRecord] = []
        async for item in items:
            try:
                doc = MembershipDoc.model_validate(item)
            except Exception:
                continue
            records.append(membership_doc_to_record(doc))
        return records

    async def list_memberships_by_user(self, user_id: str) -> list[MembershipRecord]:
        items = self._memberships_container.query_items(
            query=("SELECT * FROM c WHERE c.user_id = @user_id"),
            parameters=[{"name": "@user_id", "value": user_id}],
            partition_key=user_id,
        )
        records: list[MembershipRecord] = []
        async for item in items:
            try:
                doc = MembershipDoc.model_validate(item)
            except Exception:
                continue
            records.append(membership_doc_to_record(doc))
        return records

    async def get_membership_for_user(
        self, tenant_id: str, user_id: str
    ) -> MembershipRecord | None:
        items = self._memberships_container.query_items(
            query=(
                "SELECT * FROM c WHERE c.tenant_id = @tenant_id AND c.user_id = @user_id"
            ),
            parameters=[
                {"name": "@tenant_id", "value": tenant_id},
                {"name": "@user_id", "value": user_id},
            ],
            partition_key=tenant_id,
        )
        async for item in items:
            try:
                doc = MembershipDoc.model_validate(item)
            except Exception:
                return None
            return membership_doc_to_record(doc)
        return None

    async def save_user(self, record: UserRecord) -> None:
        if not record.id:
            raise ValueError("UserRecord.id is required for persistence")
        pk = user_partition(record.id)
        doc = user_record_to_doc(record)
        await self._users_container.upsert_item(
            doc.model_dump(by_alias=True, exclude_none=True),
            partition_key=pk,
        )

    async def save_user_identity(self, record: UserIdentityRecord) -> None:
        doc = user_identity_record_to_doc(record)
        await self._identities_container.upsert_item(
            doc.model_dump(by_alias=True, exclude_none=True)
        )

    async def save_membership(self, record: MembershipRecord) -> None:
        doc = membership_record_to_doc(record)
        await self._memberships_container.upsert_item(
            doc.model_dump(by_alias=True, exclude_none=True)
        )

    async def save_tenant(self, record: TenantRecord) -> None:
        from app.infra.mapper.authz_mapper import tenant_record_to_doc

        doc = tenant_record_to_doc(record)
        await self._tenants_container.upsert_item(
            doc.model_dump(by_alias=True, exclude_none=True),
            partition_key=record.id,
        )

    async def _read_user_item(self, user_id: str) -> UserRecord | None:
        """Fetch the user record by user id.

        Args:
            user_id: User identifier.

        Returns:
            UserRecord | None: User record or None.
        """
        pk = user_partition(user_id)
        try:
            item = await self._users_container.read_item(item=user_id, partition_key=pk)
        except Exception:
            return None
        try:
            doc = UserDoc.model_validate(item)
        except Exception:
            return None
        return user_doc_to_record(doc)

    async def _read_tenant_item(self, tenant_id: str) -> TenantRecord | None:
        """Fetch the tenant record by tenant id.

        Args:
            tenant_id: Tenant identifier.

        Returns:
            TenantRecord | None: Tenant record or None.
        """
        try:
            item = await self._tenants_container.read_item(
                item=tenant_id,
                partition_key=tenant_id,
            )
        except Exception:
            return None
        try:
            doc = TenantDoc.model_validate(item)
        except Exception:
            return None
        return tenant_doc_to_record(doc)

    async def _read_user_identity_item(self, identity_id: str) -> UserIdentityRecord | None:
        try:
            item = await self._identities_container.read_item(
                item=identity_id,
                partition_key=identity_id,
            )
        except Exception:
            return None
        try:
            doc = UserIdentityDoc.model_validate(item)
        except Exception:
            return None
        return user_identity_doc_to_record(doc)
