import pytest

from app.features.authz.models import (
    MembershipRecord,
    MembershipStatus,
    TenantRecord,
    ToolOverridesRecord,
    UserIdentityRecord,
    UserInfo,
    UserRecord,
)
from app.features.authz.ports import AuthzRepository
from app.features.authz.service import AuthzService


class SpyAuthzRepository(AuthzRepository):
    def __init__(
        self,
        *,
        users: dict[str, UserRecord] | None = None,
        tenants: dict[str, TenantRecord] | None = None,
        identities: dict[str, UserIdentityRecord] | None = None,
        memberships: list[MembershipRecord] | None = None,
    ) -> None:
        self._users = users or {}
        self._tenants = tenants or {}
        self._identities = identities or {}
        self._memberships = memberships or []
        self.saved_user: UserRecord | None = None
        self.saved_identity: UserIdentityRecord | None = None
        self.saved_membership: MembershipRecord | None = None

    async def get_user(self, user_id: str) -> UserRecord | None:
        return self._users.get(user_id)

    async def get_tenant(self, tenant_id: str) -> TenantRecord | None:
        return self._tenants.get(tenant_id)

    async def get_user_identity(self, identity_id: str) -> UserIdentityRecord | None:
        return self._identities.get(identity_id)

    async def list_memberships_by_email(
        self, email: str, status: MembershipStatus
    ) -> list[MembershipRecord]:
        return [
            record
            for record in self._memberships
            if record.invite_email == email and record.status == status
        ]

    async def list_memberships_by_user(self, user_id: str) -> list[MembershipRecord]:
        return [record for record in self._memberships if record.user_id == user_id]

    async def get_membership_for_user(
        self, tenant_id: str, user_id: str
    ) -> MembershipRecord | None:
        for record in self._memberships:
            if record.tenant_id == tenant_id and record.user_id == user_id:
                return record
        return None

    async def save_user(self, record: UserRecord) -> None:
        self.saved_user = record
        self._users[record.id] = record

    async def save_user_identity(self, record: UserIdentityRecord) -> None:
        self.saved_identity = record
        self._identities[record.id] = record

    async def save_membership(self, record: MembershipRecord) -> None:
        self.saved_membership = record


def _build_user_info() -> UserInfo:
    return UserInfo(
        id="identity-001",
        email="user001@example.com",
        provider="local",
        first_name="Taro",
        last_name="Yamada",
    )


@pytest.mark.asyncio
async def test_resolve_access_existing_identity_returns_records() -> None:
    tenant = TenantRecord(
        id="tenant-001",
        name="Tenant 001",
        default_tool_ids=["tool-01"],
    )
    user = UserRecord(
        active_tenant_id=tenant.id,
        id="user-001",
        email="user001@example.com",
        first_name="Taro",
        last_name="Yamada",
    )
    identity = UserIdentityRecord(
        id="identity-001",
        provider="local",
        user_id=user.id,
    )
    membership = MembershipRecord(
        id="member-001",
        tenant_id=tenant.id,
        user_id=user.id,
        status=MembershipStatus.ACTIVE,
        tool_overrides=ToolOverridesRecord(),
    )
    repo = SpyAuthzRepository(
        users={user.id: user},
        tenants={tenant.id: tenant},
        identities={identity.id: identity},
        memberships=[membership],
    )
    service = AuthzService(repo)

    result = await service.resolve_access(_build_user_info())

    assert result.user_record == user
    assert result.tenant_record == tenant
    assert result.user_identity == identity
    assert result.membership == membership
    assert repo.saved_user is None
    assert repo.saved_identity is None
    assert repo.saved_membership is None


@pytest.mark.asyncio
async def test_resolve_access_membership_creates_user_and_identity() -> None:
    tenant = TenantRecord(
        id="tenant-001",
        name="Tenant 001",
        default_tool_ids=["tool-01"],
    )
    membership = MembershipRecord(
        id="prov-001",
        invite_email="user001@example.com",
        tenant_id=tenant.id,
        tool_overrides=ToolOverridesRecord(allow=["tool-02"]),
        status=MembershipStatus.PENDING,
    )
    repo = SpyAuthzRepository(
        tenants={tenant.id: tenant},
        memberships=[membership],
    )
    service = AuthzService(repo)

    result = await service.resolve_access(_build_user_info())

    assert repo.saved_user is not None
    assert repo.saved_user.active_tenant_id == tenant.id
    assert repo.saved_user.email == membership.invite_email
    assert repo.saved_identity is not None
    assert repo.saved_identity.user_id == repo.saved_user.id
    assert repo.saved_membership is not None
    assert repo.saved_membership.status == MembershipStatus.ACTIVE
    assert repo.saved_membership.user_id == repo.saved_user.id
    assert result.user_record == repo.saved_user
    assert result.tenant_record == tenant
    assert result.user_identity == repo.saved_identity
