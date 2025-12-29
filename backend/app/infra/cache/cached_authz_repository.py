import asyncio
from logging import getLogger

from app.features.authz.models import (
    ProvisioningRecord,
    ProvisioningStatus,
    TenantRecord,
    UserIdentityRecord,
    UserRecord,
)
from app.features.authz.ports import AuthzRepository
from app.infra.cache.lru_cache import LruTtlCache

logger = getLogger(__name__)


class CachedAuthzRepository(AuthzRepository):
    def __init__(self, repo: AuthzRepository, ttl_seconds: int, max_size: int) -> None:
        self._repo = repo
        self._lock = asyncio.Lock()
        self._user_cache: LruTtlCache[UserRecord] = LruTtlCache(ttl_seconds, max_size)
        self._tenant_cache: LruTtlCache[TenantRecord] = LruTtlCache(ttl_seconds, max_size)
        self._identity_cache: LruTtlCache[UserIdentityRecord] = LruTtlCache(ttl_seconds, max_size)

    async def get_user(self, user_id: str) -> UserRecord | None:
        if not self._user_cache.is_enabled():
            return await self._repo.get_user(user_id)

        async with self._lock:
            result = self._user_cache.get(user_id)

        if result.hit:
            logger.debug(
                f"Cache hit for user_id={user_id}. Remeing TTL={result.remaining_ttl:.2f}s"
            )
            return result.value

        value = await self._repo.get_user(user_id)

        async with self._lock:
            self._user_cache.set(user_id, value)

        return value

    async def get_tenant(self, tenant_id: str) -> TenantRecord | None:
        if not self._tenant_cache.is_enabled():
            return await self._repo.get_tenant(tenant_id)

        async with self._lock:
            result = self._tenant_cache.get(tenant_id)

        if result.hit:
            logger.debug(
                f"Cache hit for tenant_id={tenant_id}. Remeing TTL={result.remaining_ttl:.2f}s"
            )
            return result.value

        value = await self._repo.get_tenant(tenant_id)

        async with self._lock:
            self._tenant_cache.set(tenant_id, value)

        return value

    async def get_user_identity(self, identity_id: str) -> UserIdentityRecord | None:
        if not self._identity_cache.is_enabled():
            return await self._repo.get_user_identity(identity_id)

        async with self._lock:
            result = self._identity_cache.get(identity_id)

        if result.hit:
            logger.debug(
                f"Cache hit for identity_id={identity_id}. Remeing TTL={result.remaining_ttl:.2f}s"
            )
            return result.value

        value = await self._repo.get_user_identity(identity_id)

        async with self._lock:
            self._identity_cache.set(identity_id, value)

        return value

    async def list_provisioning_by_email(
        self, email: str, status: ProvisioningStatus
    ) -> list[ProvisioningRecord]:
        return await self._repo.list_provisioning_by_email(email, status)

    async def save_user(self, record: UserRecord) -> None:
        await self._repo.save_user(record)

    async def save_user_identity(self, record: UserIdentityRecord) -> None:
        await self._repo.save_user_identity(record)

    async def save_provisioning(self, record: ProvisioningRecord) -> None:
        await self._repo.save_provisioning(record)
