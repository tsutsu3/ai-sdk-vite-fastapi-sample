import json

from azure.core.credentials import AzureNamedKeyCredential
from azure.eventhub import EventData
from azure.eventhub.aio import EventHubProducerClient

from app.core.config import AppConfig
from app.features.usage.models import UsageRecord
from app.features.usage.ports import UsageRepository
from app.shared.time import now_datetime


class AzureEventHubUsageRepository(UsageRepository):
    """Azure Event Hub usage repository (no local buffering)."""

    def __init__(
        self,
        config: AppConfig,
        producer: EventHubProducerClient,
    ) -> None:
        self._event_data_cls = EventData
        self._producer = producer

        if not (
            config.usage_eventhub_namespace
            and config.usage_eventhub_key_name
            and config.usage_eventhub_api_key
        ):
            raise RuntimeError("Usage Event Hub API key settings are not configured.")
        credential = AzureNamedKeyCredential(
            config.usage_eventhub_key_name,
            config.usage_eventhub_api_key,
        )
        self._producer = EventHubProducerClient(
            fully_qualified_namespace=config.usage_eventhub_namespace,
            credential=credential,
            eventhub_name=config.usage_eventhub_name or None,
        )

    async def record_usage(self, record: UsageRecord) -> None:
        recorded_at = now_datetime()
        payload = record.model_dump(mode="json")
        payload["recorded_at"] = recorded_at.isoformat()
        payload["dt"] = recorded_at.date().isoformat()
        line = json.dumps(payload, ensure_ascii=True, separators=(",", ":"))

        batch = await self._producer.create_batch()
        try:
            batch.add(self._event_data_cls(line))
        except ValueError as exc:
            raise RuntimeError("Usage record exceeds the maximum Event Hub batch size.") from exc
        await self._producer.send_batch(batch)

    async def flush(self) -> None:
        return None
