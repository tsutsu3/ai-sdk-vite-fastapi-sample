import asyncio
import time
from collections import OrderedDict
from typing import Generic, TypeVar

from app.infra.cache.cache_provider import CacheProvider

T = TypeVar("T")


class _CacheEntry(Generic[T]):
    """Internal cache entry with expiry."""

    def __init__(self, value: T | None, expires_at: float) -> None:
        self.value = value
        self.expires_at = expires_at


class MemoryCacheProvider(CacheProvider[T]):
    """In-memory cache provider using LRU eviction."""

    def __init__(self, max_size: int = 1000) -> None:
        """Initialize memory cache provider.

        Args:
            max_size: Maximum number of entries in cache.
        """
        self._max_size = max_size
        self._store: OrderedDict[str, _CacheEntry[T]] = OrderedDict()
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> T | None:
        """Get value from cache by key."""
        async with self._lock:
            entry = self._store.get(key)
            if not entry:
                return None

            # Check if expired
            now = time.monotonic()
            if entry.expires_at <= now:
                self._store.pop(key, None)
                return None

            # Move to end (mark as recently used)
            self._store.move_to_end(key)
            return entry.value

    async def set(self, key: str, value: T | None, ttl_seconds: int) -> None:
        """Set value in cache with TTL."""
        async with self._lock:
            expires_at = time.monotonic() + ttl_seconds

            # Remove existing entry if present
            self._store.pop(key, None)

            # Add new entry
            self._store[key] = _CacheEntry(value=value, expires_at=expires_at)
            self._store.move_to_end(key)

            # Evict oldest entries if max size exceeded
            while len(self._store) > self._max_size:
                self._store.popitem(last=False)

    async def delete(self, key: str) -> None:
        """Delete value from cache."""
        async with self._lock:
            self._store.pop(key, None)

    async def close(self) -> None:
        """Close cache connections and cleanup resources."""
        async with self._lock:
            self._store.clear()

    def is_enabled(self) -> bool:
        """Check if cache is enabled."""
        return self._max_size > 0
