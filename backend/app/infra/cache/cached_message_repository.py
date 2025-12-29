import asyncio
import json
from logging import getLogger

from app.features.messages.models import MessageRecord
from app.features.messages.ports import MessageRepository
from app.infra.cache.lru_cache import LruTtlCache

logger = getLogger(__name__)

_CACHE_TOKEN_PREFIX = "cache:"


class CachedMessageRepository(MessageRepository):
    """Message repository decorator that hides cache behavior from callers.

    We only cache full conversation lists so paging stays consistent, and we
    merge write-sets into the cached list to keep it coherent without re-reading.
    """

    def __init__(self, repo: MessageRepository, ttl_seconds: int, max_bytes: int) -> None:
        self._repo = repo
        self._lock = asyncio.Lock()
        self._cache = LruTtlCache(
            ttl_seconds,
            max_size=1000000,  # Large number to avoid size-based evictions
            max_bytes=max_bytes,
            size_estimator=self._estimate_messages_bytes,
        )

    def _cache_key(self, tenant_id: str, user_id: str, conversation_id: str) -> str:
        return f"{tenant_id}:{user_id}:{conversation_id}"

    def _estimate_messages_bytes(self, messages: list[MessageRecord] | None) -> int:
        if not messages:
            return 0
        payload = [
            message.model_dump(by_alias=True, exclude_none=True, mode="json")
            for message in messages
        ]
        return len(json.dumps(payload, ensure_ascii=True).encode("utf-8"))

    def _merge_messages(
        self,
        existing: list[MessageRecord],
        incoming: list[MessageRecord],
    ) -> list[MessageRecord]:
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

        async with self._lock:
            result = self._cache.get(cache_key, refresh_ttl=True)
        if result.hit:
            logger.debug(
                "Cache hit for conversation_id=%s. message count=%d. messages bytes=%d",
                conversation_id,
                len(result.value or []),
                result.byte_size or 0,
            )
        if (
            result.hit
            and result.value is not None
            and (continuation_token is None or use_cache_token)
        ):
            # Cache hit: we serve pages from the cached full list so pagination
            # stays consistent with earlier pages emitted from this cache.
            return self._slice_messages(
                result.value,
                limit=limit,
                continuation_token=continuation_token if use_cache_token else None,
                descending=descending,
            )

        if continuation_token and not use_cache_token:
            # We must honor the storage continuation token to avoid paging drift,
            # so we bypass the cache entirely when the caller owns the token.
            return await self._repo.list_messages(
                tenant_id,
                user_id,
                conversation_id,
                limit=limit,
                continuation_token=continuation_token,
                descending=descending,
            )

        if limit is not None:
            # For partial lists we skip caching to avoid creating a "partial"
            # cache that would break later pagination or merge semantics.
            return await self._repo.list_messages(
                tenant_id,
                user_id,
                conversation_id,
                limit=limit,
                continuation_token=continuation_token,
                descending=descending,
            )

        messages = await self._load_full_conversation(tenant_id, user_id, conversation_id)

        async with self._lock:
            self._cache.set(cache_key, messages)

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
        stored = await self._repo.upsert_messages(tenant_id, user_id, conversation_id, messages)
        if not self._cache.is_enabled():
            return stored

        cache_key = self._cache_key(tenant_id, user_id, conversation_id)
        async with self._lock:
            result = self._cache.get(cache_key, refresh_ttl=True)
            if not result.hit or result.value is None:
                return stored
            # Keep list caches consistent with writes by merging the write-set
            # into the cached full list instead of re-reading all pages.
            merged = self._merge_messages(result.value, stored)
            self._cache.set(cache_key, merged)
        return stored

    async def delete_messages(self, tenant_id: str, user_id: str, conversation_id: str) -> None:
        await self._repo.delete_messages(tenant_id, user_id, conversation_id)
        if not self._cache.is_enabled():
            return
        cache_key = self._cache_key(tenant_id, user_id, conversation_id)
        async with self._lock:
            self._cache.set(cache_key, [])

    async def update_message_reaction(
        self,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
        message_id: str,
        reaction: str | None,
    ) -> MessageRecord | None:
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
        async with self._lock:
            result = self._cache.get(cache_key, refresh_ttl=True)
            if not result.hit or result.value is None:
                return updated
            merged = self._merge_messages(result.value, [updated])
            self._cache.set(cache_key, merged)
        return updated
