import json
from logging import getLogger
from typing import Any, TypeVar

from pydantic import BaseModel

from app.infra.cache.cache_provider import CacheProvider

T = TypeVar("T")

logger = getLogger(__name__)


class RedisCacheProvider(CacheProvider[T]):
    """Redis cache provider with JSON serialization."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: str | None = None,
        ssl: bool = False,
        decode_responses: bool = True,
    ) -> None:
        """Initialize Redis cache provider.

        Args:
            host: Redis host.
            port: Redis port.
            db: Redis database number.
            password: Redis password (optional).
            ssl: Use SSL connection.
            decode_responses: Decode responses to strings.
        """
        self._host = host
        self._port = port
        self._db = db
        self._password = password
        self._ssl = ssl
        self._decode_responses = decode_responses
        self._client: Any = None

    async def _get_client(self) -> Any:
        """Get or create Redis client."""
        if self._client is not None:
            return self._client

        try:
            import redis.asyncio as redis
        except ImportError as exc:
            raise RuntimeError(
                "redis package is required for RedisCacheProvider. "
                "Install with: pip install redis"
            ) from exc

        self._client = redis.Redis(
            host=self._host,
            port=self._port,
            db=self._db,
            password=self._password,
            ssl=self._ssl,
            decode_responses=self._decode_responses,
        )
        return self._client

    def _serialize(self, value: T | None) -> str:
        """Serialize value to JSON string."""
        if value is None:
            return json.dumps(None)
        if isinstance(value, BaseModel):
            return value.model_dump_json(by_alias=True, exclude_none=True)
        if isinstance(value, list):
            # Handle list of Pydantic models
            if value and isinstance(value[0], BaseModel):
                return json.dumps(
                    [
                        item.model_dump(by_alias=True, exclude_none=True, mode="json")
                        for item in value
                    ]
                )
        return json.dumps(value)

    def _deserialize(self, data: str | None, model_class: type[T] | None = None) -> T | None:
        """Deserialize JSON string to value."""
        if data is None:
            return None

        parsed = json.loads(data)
        if parsed is None:
            return None

        # If model_class is provided, validate/parse the data
        if model_class is not None and isinstance(parsed, dict):
            return model_class.model_validate(parsed)  # type: ignore

        return parsed  # type: ignore

    async def get(self, key: str) -> T | None:
        """Get value from Redis by key."""
        try:
            client = await self._get_client()
            data = await client.get(key)
            if data is None:
                return None
            return self._deserialize(data)
        except Exception as exc:
            logger.warning("Redis get failed for key=%s: %s", key, exc)
            return None

    async def set(self, key: str, value: T | None, ttl_seconds: int) -> None:
        """Set value in Redis with TTL."""
        try:
            client = await self._get_client()
            serialized = self._serialize(value)
            await client.setex(key, ttl_seconds, serialized)
        except Exception as exc:
            logger.warning("Redis set failed for key=%s: %s", key, exc)

    async def delete(self, key: str) -> None:
        """Delete value from Redis."""
        try:
            client = await self._get_client()
            await client.delete(key)
        except Exception as exc:
            logger.warning("Redis delete failed for key=%s: %s", key, exc)

    async def close(self) -> None:
        """Close Redis connection."""
        if self._client is not None:
            try:
                await self._client.aclose()
            except Exception as exc:
                logger.warning("Redis close failed: %s", exc)
            finally:
                self._client = None

    def is_enabled(self) -> bool:
        """Check if cache is enabled."""
        return True
