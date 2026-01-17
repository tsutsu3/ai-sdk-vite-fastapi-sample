from logging import getLogger

from app.features.messages.models import MessageRecord
from app.features.messages.ports import MessageRepository
from app.infra.cache.cache_provider import CacheProvider

logger = getLogger(__name__)

_CACHE_TOKEN_PREFIX = "cache:"


class CachedMessageRepository(MessageRepository):
    """Message repository with pluggable cache provider.

    Caches full conversation message lists for consistent pagination.
    """

    def __init__(
        self,
        repo: MessageRepository,
        cache_provider: CacheProvider[list[MessageRecord]],
        ttl_seconds: int,
    ) -> None:
        """Initialize cached message repository.

        Args:
            repo: Underlying message repository.
            cache_provider: Cache provider implementation.
            ttl_seconds: Cache TTL in seconds.
        """
        self._repo = repo
        self._cache = cache_provider
        self._ttl_seconds = ttl_seconds

    def _cache_key(self, tenant_id: str, user_id: str, conversation_id: str) -> str:
        return f"messages:{tenant_id}:{user_id}:{conversation_id}"

    def _merge_messages(
        self,
        existing: list[MessageRecord],
        incoming: list[MessageRecord],
    ) -> list[MessageRecord]:
        """Merge incoming messages into existing list."""
        merged = list(existing)
        index_by_id = {message.id: idx for idx, message in enumerate(merged)}
        for message in incoming:
            if message.id in index_by_id:
                merged[index_by_id[message.id]] = message
            else:
                index_by_id[message.id] = len(merged)
                merged.append(message)
        return merged

    def _slice_messages(
        self,
        messages: list[MessageRecord],
        *,
        limit: int | None,
        continuation_token: str | None,
        descending: bool,
    ) -> tuple[list[MessageRecord], str | None]:
        """Slice messages for pagination."""
        ordered = list(reversed(messages)) if descending else list(messages)
        offset = 0
        if continuation_token and continuation_token.startswith(_CACHE_TOKEN_PREFIX):
            raw_offset = continuation_token[len(_CACHE_TOKEN_PREFIX) :]
            try:
                offset = max(int(raw_offset), 0)
            except ValueError:
                offset = 0
        if limit is None:
            return (ordered, None)
        safe_limit = max(limit, 0)
        sliced = ordered[offset : offset + safe_limit]
        next_offset = offset + len(sliced)
        next_token = f"{_CACHE_TOKEN_PREFIX}{next_offset}" if next_offset < len(ordered) else None
        return (sliced, next_token)

    async def _load_full_conversation(
        self, tenant_id: str, user_id: str, conversation_id: str
    ) -> list[MessageRecord]:
        """Load full conversation from repository."""
        messages, _ = await self._repo.list_messages(
            tenant_id,
            user_id,
            conversation_id,
            limit=None,
            continuation_token=None,
            descending=False,
        )
        return messages

    async def list_messages(
        self,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
        limit: int | None = None,
        continuation_token: str | None = None,
        descending: bool = False,
    ) -> tuple[list[MessageRecord], str | None]:
        """List messages with caching."""
        if not self._cache.is_enabled():
            return await self._repo.list_messages(
                tenant_id,
                user_id,
                conversation_id,
                limit=limit,
                continuation_token=continuation_token,
                descending=descending,
            )

        cache_key = self._cache_key(tenant_id, user_id, conversation_id)
        use_cache_token = continuation_token and continuation_token.startswith(
            _CACHE_TOKEN_PREFIX
        )

        # Try cache
        cached = await self._cache.get(cache_key)
        if cached is not None and (continuation_token is None or use_cache_token):
            logger.debug(
                "Cache hit for conversation_id=%s. message count=%d",
                conversation_id,
                len(cached),
            )
            return self._slice_messages(
                cached,
                limit=limit,
                continuation_token=continuation_token if use_cache_token else None,
                descending=descending,
            )

        # Bypass cache if continuation token from storage
        if continuation_token and not use_cache_token:
            logger.debug(
                "Cache bypass for conversation_id=%s reason=storage_token",
                conversation_id,
            )
            return await self._repo.list_messages(
                tenant_id,
                user_id,
                conversation_id,
                limit=limit,
                continuation_token=continuation_token,
                descending=descending,
            )

        # Skip caching for partial lists
        if limit is not None:
            logger.debug(
                "Cache bypass for conversation_id=%s reason=partial_list limit=%s",
                conversation_id,
                limit,
            )
            return await self._repo.list_messages(
                tenant_id,
                user_id,
                conversation_id,
                limit=limit,
                continuation_token=continuation_token,
                descending=descending,
            )

        # Load full conversation and cache
        messages = await self._load_full_conversation(tenant_id, user_id, conversation_id)
        await self._cache.set(cache_key, messages, self._ttl_seconds)

        return self._slice_messages(
            messages,
            limit=limit,
            continuation_token=None,
            descending=descending,
        )

    async def upsert_messages(
        self,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
        messages: list[MessageRecord],
    ) -> list[MessageRecord]:
        """Upsert messages and update cache."""
        stored = await self._repo.upsert_messages(tenant_id, user_id, conversation_id, messages)

        if not self._cache.is_enabled():
            return stored

        cache_key = self._cache_key(tenant_id, user_id, conversation_id)
        cached = await self._cache.get(cache_key)

        if cached is not None:
            # Merge into cached list
            merged = self._merge_messages(cached, stored)
            await self._cache.set(cache_key, merged, self._ttl_seconds)

        return stored

    async def delete_messages(self, tenant_id: str, user_id: str, conversation_id: str) -> None:
        """Delete messages and invalidate cache."""
        await self._repo.delete_messages(tenant_id, user_id, conversation_id)

        if self._cache.is_enabled():
            cache_key = self._cache_key(tenant_id, user_id, conversation_id)
            await self._cache.delete(cache_key)

    async def update_message_reaction(
        self,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
        message_id: str,
        reaction: str | None,
    ) -> MessageRecord | None:
        """Update message reaction and update cache."""
        updated = await self._repo.update_message_reaction(
            tenant_id,
            user_id,
            conversation_id,
            message_id,
            reaction,
        )

        if not self._cache.is_enabled() or updated is None:
            return updated

        cache_key = self._cache_key(tenant_id, user_id, conversation_id)
        cached = await self._cache.get(cache_key)

        if cached is not None:
            # Merge updated message into cache
            merged = self._merge_messages(cached, [updated])
            await self._cache.set(cache_key, merged, self._ttl_seconds)

        return updated
