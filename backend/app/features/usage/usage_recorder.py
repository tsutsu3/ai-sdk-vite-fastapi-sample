from app.features.usage.models import UsageRecord
from app.features.usage.ports import UsageRepository


class UsageRecorder:
    def __init__(self, repo: UsageRepository) -> None:
        self._repo = repo

    async def record(self, record: UsageRecord) -> None:
        await self._repo.record_usage(record)
