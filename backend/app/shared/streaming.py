from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable
from typing import TypeVar

T = TypeVar("T")


async def stream_with_lifecycle(
    stream: AsyncIterator[T],
    *,
    is_disconnected: Callable[[], Awaitable[bool]],
    idle_timeout: float,
    logger,
    stream_name: str,
) -> AsyncIterator[T]:
    """Yield items while handling disconnects, idle timeouts, and cleanup."""
    was_cancelled = False
    try:
        while True:
            if await is_disconnected():
                logger.info("%s.stream.disconnected", stream_name)
                break
            try:
                chunk = await asyncio.wait_for(
                    stream.__anext__(),
                    timeout=idle_timeout,
                )
            except StopAsyncIteration:
                break
            except asyncio.TimeoutError:
                logger.warning(
                    "%s.stream.timeout idle_seconds=%s",
                    stream_name,
                    idle_timeout,
                )
                break
            yield chunk
    except asyncio.CancelledError:
        was_cancelled = True
        logger.info("%s.stream.cancelled", stream_name)
        raise
    finally:
        aclose = getattr(stream, "aclose", None)
        if callable(aclose):
            try:
                if not was_cancelled:
                    await aclose()
            except RuntimeError:
                if not was_cancelled:
                    logger.exception("%s.stream.cleanup_failed", stream_name)
            except Exception:
                logger.exception("%s.stream.cleanup_failed", stream_name)
