from logging import getLogger

from app.features.authz.models import (
    MembershipRecord,
    MembershipStatus,
    TenantRecord,
    UserIdentityRecord,
    UserRecord,
)
from app.features.authz.ports import AuthzRepository
from app.infra.cache.cache_provider import CacheProvider

logger = getLogger(__name__)


class CachedAuthzRepository(AuthzRepository):
    """Authz repository with pluggable cache provider."""

    def __init__(
        self,
        repo: AuthzRepository,
        cache_provider: CacheProvider[UserRecord | TenantRecord | UserIdentityRecord],
        ttl_seconds: int,
    ) -> None:
        """Initialize cached authz repository.

        Args:
            repo: Underlying authz repository.
            cache_provider: Cache provider implementation.
            ttl_seconds: Cache TTL in seconds.
        """
        self._repo = repo
        self._cache = cache_provider
        self._ttl_seconds = ttl_seconds

    def _user_key(self, user_id: str) -> str:
        return f"authz:user:{user_id}"

    def _tenant_key(self, tenant_id: str) -> str:
        return f"authz:tenant:{tenant_id}"

    def _identity_key(self, identity_id: str) -> str:
        return f"authz:identity:{identity_id}"

    async def get_user(self, user_id: str) -> UserRecord | None:
        """Get user record with caching."""
        if not self._cache.is_enabled():
            return await self._repo.get_user(user_id)

        cache_key = self._user_key(user_id)
        cached = await self._cache.get(cache_key)

        if cached is not None:
            logger.debug("Cache hit for user_id=%s", user_id)
            return cached  # type: ignore

        value = await self._repo.get_user(user_id)
        if value is not None:
            await self._cache.set(cache_key, value, self._ttl_seconds)

        return value

    async def get_tenant(self, tenant_id: str) -> TenantRecord | None:
        """Get tenant record with caching."""
        if not self._cache.is_enabled():
            return await self._repo.get_tenant(tenant_id)

        cache_key = self._tenant_key(tenant_id)
        cached = await self._cache.get(cache_key)

        if cached is not None:
            logger.debug("Cache hit for tenant_id=%s", tenant_id)
            return cached  # type: ignore

        value = await self._repo.get_tenant(tenant_id)
        if value is not None:
            await self._cache.set(cache_key, value, self._ttl_seconds)

        return value

    async def get_user_identity(self, identity_id: str) -> UserIdentityRecord | None:
        """Get user identity record with caching."""
        if not self._cache.is_enabled():
            return await self._repo.get_user_identity(identity_id)

        cache_key = self._identity_key(identity_id)
        cached = await self._cache.get(cache_key)

        if cached is not None:
            logger.debug("Cache hit for identity_id=%s", identity_id)
            return cached  # type: ignore

        value = await self._repo.get_user_identity(identity_id)
        if value is not None:
            await self._cache.set(cache_key, value, self._ttl_seconds)

        return value

    async def list_memberships_by_email(
        self, email: str, status: MembershipStatus
    ) -> list[MembershipRecord]:
        """List memberships by email (not cached)."""
        return await self._repo.list_memberships_by_email(email, status)

    async def list_memberships_by_user(self, user_id: str) -> list[MembershipRecord]:
        """List memberships by user id (not cached)."""
        return await self._repo.list_memberships_by_user(user_id)

    async def get_membership_for_user(
        self, tenant_id: str, user_id: str
    ) -> MembershipRecord | None:
        """Get membership by tenant/user (not cached)."""
        return await self._repo.get_membership_for_user(tenant_id, user_id)

    async def save_user(self, record: UserRecord) -> None:
        """Save user record and invalidate cache."""
        await self._repo.save_user(record)
        if record.id and self._cache.is_enabled():
            cache_key = self._user_key(record.id)
            await self._cache.delete(cache_key)

    async def save_user_identity(self, record: UserIdentityRecord) -> None:
        """Save user identity record and invalidate cache."""
        await self._repo.save_user_identity(record)
        if self._cache.is_enabled():
            cache_key = self._identity_key(record.id)
            await self._cache.delete(cache_key)

    async def save_membership(self, record: MembershipRecord) -> None:
        """Save membership record (not cached)."""
        await self._repo.save_membership(record)

    async def save_tenant(self, record: TenantRecord) -> None:
        """Save tenant record and invalidate cache."""
        await self._repo.save_tenant(record)
        if self._cache.is_enabled():
            cache_key = self._tenant_key(record.id)
            await self._cache.delete(cache_key)

