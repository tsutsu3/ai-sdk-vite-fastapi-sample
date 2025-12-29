from typing import Protocol

from app.features.authz.models import (
    ProvisioningRecord,
    ProvisioningStatus,
    TenantRecord,
    UserIdentityRecord,
    UserRecord,
)


class AuthzRepository(Protocol):
    """Interface for authorization data lookup.

    This abstraction isolates permission storage so API handlers can query
    a single interface regardless of whether authz data is in memory, Cosmos,
    or another backend.
    """

    async def get_user(self, user_id: str) -> UserRecord | None:
        """Fetch user data for authorization.

        Args:
            user_id: Unique user identifier.

        Returns:
            UserRecord | None: User record or None if missing.
        """
        raise NotImplementedError

    async def get_tenant(self, tenant_id: str) -> TenantRecord | None:
        """Fetch tenant data for authorization.

        Args:
            tenant_id: Tenant identifier.

        Returns:
            TenantRecord | None: Tenant record or None if missing.
        """
        raise NotImplementedError

    async def get_user_identity(self, identity_id: str) -> UserIdentityRecord | None:
        """Fetch identity data for an authn user id.

        Args:
            identity_id: Auth provider user id.

        Returns:
            UserIdentityRecord | None: Identity record or None if missing.
        """
        raise NotImplementedError

    async def list_provisioning_by_email(
        self, email: str, status: ProvisioningStatus
    ) -> list[ProvisioningRecord]:
        """List provisioning records by email and status.

        Args:
            email: User email address.
            status: Provisioning status to match.

        Returns:
            list[ProvisioningRecord]: Matching provisioning records.
        """
        raise NotImplementedError

    async def save_user(self, record: UserRecord) -> None:
        """Persist a user record."""
        raise NotImplementedError

    async def save_user_identity(self, record: UserIdentityRecord) -> None:
        """Persist a user identity record."""
        raise NotImplementedError

    async def save_provisioning(self, record: ProvisioningRecord) -> None:
        """Persist a provisioning record."""
        raise NotImplementedError
