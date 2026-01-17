"""Cache provider factory for creating cache instances based on configuration."""

from logging import getLogger

from app.core.config import AppConfig, CacheBackend
from app.infra.cache.cache_provider import CacheProvider
from app.infra.cache.memory_cache_provider import MemoryCacheProvider
from app.infra.cache.redis_cache_provider import RedisCacheProvider

logger = getLogger(__name__)


class CacheConfig:
    """Cache configuration for specific cache type."""

    def __init__(
        self,
        ttl_seconds: int,
        max_size: int,
        redis_db: int,
        max_bytes: int | None = None,
    ) -> None:
        """Initialize cache configuration.

        Args:
            ttl_seconds: Cache TTL in seconds.
            max_size: Maximum number of entries (for memory cache).
            redis_db: Redis database number (for Redis cache).
            max_bytes: Maximum bytes (for memory cache, optional).
        """
        self.ttl_seconds = ttl_seconds
        self.max_size = max_size
        self.redis_db = redis_db
        self.max_bytes = max_bytes


class CacheProviderFactory:
    """Factory for creating cache provider instances."""

    @staticmethod
    def get_authz_config(config: AppConfig) -> CacheConfig:
        """Get authz cache configuration.

        Args:
            config: Application configuration.

        Returns:
            CacheConfig: Authz cache configuration.
        """
        return CacheConfig(
            ttl_seconds=config.authz_cache_ttl_seconds,
            max_size=config.authz_cache_max_size,
            redis_db=config.authz_redis_db,
        )

    @staticmethod
    def get_messages_config(config: AppConfig) -> CacheConfig:
        """Get messages cache configuration.

        Args:
            config: Application configuration.

        Returns:
            CacheConfig: Messages cache configuration.
        """
        return CacheConfig(
            ttl_seconds=config.messages_cache_ttl_seconds,
            max_size=config.messages_cache_max_size,
            redis_db=config.messages_redis_db,
            max_bytes=config.messages_cache_max_bytes,
        )

    @staticmethod
    def create_cache_provider(
        app_config: AppConfig,
        cache_config: CacheConfig,
        cache_name: str = "default",
    ) -> CacheProvider:
        """Create cache provider based on configuration.

        Args:
            app_config: Application configuration.
            cache_config: Cache-specific configuration.
            cache_name: Name of the cache (for logging).

        Returns:
            CacheProvider: Configured cache provider instance.

        Raises:
            ValueError: If cache backend is not supported.
        """
        cache_backend = app_config.cache_backend

        if cache_backend == CacheBackend.redis:
            logger.info(
                "Creating Redis cache provider for %s: host=%s port=%d db=%d ssl=%s ttl=%ds",
                cache_name,
                app_config.redis_host,
                app_config.redis_port,
                cache_config.redis_db,
                app_config.redis_ssl,
                cache_config.ttl_seconds,
            )
            return RedisCacheProvider(
                host=app_config.redis_host,
                port=app_config.redis_port,
                db=cache_config.redis_db,
                password=app_config.redis_password or None,
                ssl=app_config.redis_ssl,
            )

        elif cache_backend == CacheBackend.memory:
            logger.info(
                "Creating Memory cache provider for %s: max_size=%d ttl=%ds",
                cache_name,
                cache_config.max_size,
                cache_config.ttl_seconds,
            )
            return MemoryCacheProvider(max_size=cache_config.max_size)

        elif cache_backend == CacheBackend.off:
            logger.info("Cache disabled for %s", cache_name)
            return MemoryCacheProvider(max_size=0)

        else:
            raise ValueError(f"Unsupported cache backend: {cache_backend}")

    @staticmethod
    def create_authz_cache_provider(config: AppConfig) -> CacheProvider:
        """Create cache provider for authz.

        Args:
            config: Application configuration.

        Returns:
            CacheProvider: Authz cache provider.
        """
        cache_config = CacheProviderFactory.get_authz_config(config)
        return CacheProviderFactory.create_cache_provider(
            config,
            cache_config,
            cache_name="authz",
        )

    @staticmethod
    def create_messages_cache_provider(config: AppConfig) -> CacheProvider:
        """Create cache provider for messages.

        Args:
            config: Application configuration.

        Returns:
            CacheProvider: Messages cache provider.
        """
        cache_config = CacheProviderFactory.get_messages_config(config)
        return CacheProviderFactory.create_cache_provider(
            config,
            cache_config,
            cache_name="messages",
        )
