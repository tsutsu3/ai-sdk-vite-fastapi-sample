from typing import Protocol

from app.features.usage.models import UsageRecord


class UsageRepository(Protocol):
    async def record_usage(self, record: UsageRecord) -> None:
        """Persist a usage record."""
        raise NotImplementedError
