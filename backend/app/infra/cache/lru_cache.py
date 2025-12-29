import time
from collections import OrderedDict
from typing import Callable, Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class CacheEntry(BaseModel, Generic[T]):
    """Cache entry with expiry metadata and size."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    expires_at: float
    value: T | None
    byte_size: int


class CacheResult(BaseModel, Generic[T]):
    """Result of a cache get operation."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    hit: bool | None
    value: T | None
    remaining_ttl: float  # Remaining time to live in seconds
    expires_at: float
    byte_size: int


class LruTtlCache(Generic[T]):
    """In-memory LRU cache with TTL."""

    def __init__(
        self,
        ttl_seconds: int,
        max_size: int,
        *,
        max_bytes: int | None = None,
        size_estimator: Callable[[T | None], int] | None = None,
    ) -> None:
        self._ttl_seconds = ttl_seconds
        self._max_size = max_size
        self._max_bytes = max_bytes
        self._size_estimator = size_estimator
        self._store: OrderedDict[str, CacheEntry[T]] = OrderedDict()
        self._total_bytes = 0

    def is_enabled(self) -> bool:
        if self._ttl_seconds <= 0:
            return False
        if self._max_size <= 0:
            return False
        if self._max_bytes is not None and self._max_bytes <= 0:
            return False
        return True

    def get(self, key: str, refresh_ttl: bool = True) -> CacheResult[T]:
        """Return a cache entry.

        Args:
            key: The cache key.
            refresh_ttl: Whether to refresh the TTL on access. Defaults to True.

        Returns:
            A CacheResult object containing hit status, value, and TTL remaining.
        """
        not_hit = CacheResult(
            hit=False, value=None, remaining_ttl=0.0, expires_at=0.0, byte_size=0
        )

        if not self.is_enabled():
            return not_hit

        now = time.monotonic()
        entry = self._store.get(key)
        if not entry:
            return not_hit

        # Expired cache entry
        if entry.expires_at <= now:
            self._store.pop(key, None)
            self._total_bytes -= entry.byte_size
            return not_hit

        if refresh_ttl:
            entry.expires_at = now + self._ttl_seconds

        self._store.move_to_end(key)
        return CacheResult(
            hit=True,
            value=entry.value,
            remaining_ttl=entry.expires_at - now,
            expires_at=entry.expires_at,
            byte_size=entry.byte_size,
        )

    def set(self, key: str, value: T | None) -> CacheResult[T] | None:
        """Set a cache entry.

        Args:
            key: The cache key.
            value: The value to cache.
        Returns:
            True if the cache is enabled and the entry was set, False otherwise.
        """
        if not self.is_enabled():
            return CacheResult(
                hit=None, value=None, remaining_ttl=0.0, expires_at=0.0, byte_size=0
            )

        expires_at = time.monotonic() + self._ttl_seconds
        entry_size = 0
        if self._size_estimator:
            entry_size = max(self._size_estimator(value), 0)
        existing = self._store.pop(key, None)
        if existing:
            self._total_bytes -= existing.byte_size
        self._store[key] = CacheEntry(
            expires_at=expires_at,
            value=value,
            byte_size=entry_size,
        )

        # Move to end to mark as recently used
        self._store.move_to_end(key)
        self._total_bytes += entry_size
        while len(self._store) > self._max_size:
            _, removed = self._store.popitem(last=False)
            self._total_bytes -= removed.byte_size

        # If no max bytes limit, return early
        if self._max_bytes is None:
            return CacheResult(
                hit=None,
                value=value,
                remaining_ttl=self._ttl_seconds,
                expires_at=expires_at,
                byte_size=entry_size,
            )

        while self._total_bytes > self._max_bytes and self._store:
            _, removed = self._store.popitem(last=False)
            self._total_bytes -= removed.byte_size

        # Return cache result after evictions
        return CacheResult(
            hit=None,
            value=value,
            remaining_ttl=self._ttl_seconds,
            expires_at=expires_at,
            byte_size=entry_size,
        )
