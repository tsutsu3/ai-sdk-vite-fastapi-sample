from app.features.usage.models import UsageRecord
from app.features.usage.ports import UsageRepository


class UsageRecorder:
    """Service for recording usage data.

    This service isolates usage persistence so chat execution can remain
    focused on streaming and storage backends can vary.
    """

    def __init__(self, repo: UsageRepository) -> None:
        """Initialize the usage recorder.

        Args:
            repo: Usage repository.
        """
        self._repo = repo

    async def record(self, record: UsageRecord) -> None:
        """Record usage data.

        This is intentionally thin to allow future batching or async sinks.

        Args:
            record: Usage record to persist.
        """
        await self._repo.record_usage(record)
