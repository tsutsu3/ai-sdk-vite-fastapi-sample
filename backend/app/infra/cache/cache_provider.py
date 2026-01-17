from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")


class CacheProvider(ABC, Generic[T]):
    """Abstract cache provider interface."""

    @abstractmethod
    async def get(self, key: str) -> T | None:
        """Get value from cache by key.

        Args:
            key: Cache key.

        Returns:
            Cached value or None if not found or expired.
        """
        raise NotImplementedError

    @abstractmethod
    async def set(self, key: str, value: T | None, ttl_seconds: int) -> None:
        """Set value in cache with TTL.

        Args:
            key: Cache key.
            value: Value to cache.
            ttl_seconds: Time to live in seconds.
        """
        raise NotImplementedError

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete value from cache.

        Args:
            key: Cache key.
        """
        raise NotImplementedError

    @abstractmethod
    async def close(self) -> None:
        """Close cache connections and cleanup resources."""
        raise NotImplementedError

    @abstractmethod
    def is_enabled(self) -> bool:
        """Check if cache is enabled.

        Returns:
            True if cache is enabled, False otherwise.
        """
        raise NotImplementedError
