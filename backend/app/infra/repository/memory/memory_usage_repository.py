from app.features.usage.models import UsageRecord
from app.features.usage.ports import UsageRepository


class MemoryUsageRepository(UsageRepository):
    def __init__(self) -> None:
        self._records: list[UsageRecord] = []

    async def record_usage(self, record: UsageRecord) -> None:
        self._records.append(record)
