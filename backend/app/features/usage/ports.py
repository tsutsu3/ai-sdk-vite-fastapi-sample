from typing import Protocol

from app.features.usage.models import UsageRecord


class UsageRepository(Protocol):
    """Interface for usage persistence.

    This abstraction isolates analytics/billing storage so usage recording
    can be swapped without changing chat execution code.
    """

    async def record_usage(self, record: UsageRecord) -> None:
        """Persist a usage record.

        This may be used for analytics and billing.

        Args:
            record: Usage data to store.
        """
        raise NotImplementedError
