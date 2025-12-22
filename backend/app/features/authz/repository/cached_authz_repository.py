import asyncio
import time
from collections import OrderedDict

from pydantic import BaseModel

from app.features.authz.models import AuthzRecord
from app.features.authz.repository.authz_repository import AuthzRepository


class _CacheEntry(BaseModel, frozen=True):
    expires_at: float
    value: AuthzRecord | None


class CachedAuthzRepository(AuthzRepository):
    """An AuthzRepository implementation with an in-memory TTL-based LRU cache.

    This cache stores authorization records keyed by user ID.
    Entries are considered valid until their TTL expires.
    When the cache exceeds the maximum size, the least recently usedentry is evicted.
    """

    def __init__(self, repo: AuthzRepository, ttl_seconds: int, max_size: int) -> None:
        self._repo = repo
        self._ttl_seconds = ttl_seconds
        self._max_size = max_size
        self._cache: OrderedDict[str, _CacheEntry] = OrderedDict()
        self._lock = asyncio.Lock()

    async def get_authz(self, user_id: str) -> AuthzRecord | None:
        if self._ttl_seconds <= 0 or self._max_size <= 0:
            return await self._repo.get_authz(user_id)

        # cache hit
        now = time.monotonic()
        async with self._lock:
            entry = self._cache.get(user_id)
            if entry:
                if entry.expires_at > now:
                    self._cache.move_to_end(user_id)
                    return entry.value
                self._cache.pop(user_id, None)

        # cache miss
        value = await self._repo.get_authz(user_id)
        expires_at = time.monotonic() + self._ttl_seconds

        async with self._lock:
            self._cache[user_id] = _CacheEntry(expires_at=expires_at, value=value)
            self._cache.move_to_end(user_id)
            while len(self._cache) > self._max_size:
                self._cache.popitem(last=False)

        return value
