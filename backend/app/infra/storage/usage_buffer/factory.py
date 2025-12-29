from azure.eventhub.aio import EventHubProducerClient

from app.core.config import AppConfig, UsageBufferBackend
from app.features.usage.ports import UsageRepository
from app.infra.storage.usage_buffer.azure_eventhub import AzureEventHubUsageRepository
from app.infra.storage.usage_buffer.gcs import GcsUsageRepository
from app.infra.storage.usage_buffer.local import LocalUsageRepository


def create_usage_repository(
    app_config: AppConfig,
    *,
    azure_eventhub_producer: EventHubProducerClient | None = None,
) -> UsageRepository:
    match app_config.usage_buffer_backend:
        case UsageBufferBackend.local:
            return LocalUsageRepository(
                app_config.usage_buffer_local_path,
                flush_max_records=app_config.usage_buffer_flush_max_records,
                flush_interval_seconds=app_config.usage_buffer_flush_interval_seconds,
            )
        case UsageBufferBackend.azure:
            if azure_eventhub_producer is None:
                raise RuntimeError("Azure Event Hub producer must be provided.")
            return AzureEventHubUsageRepository(
                producer=azure_eventhub_producer,
            )
        case UsageBufferBackend.gcp:
            return GcsUsageRepository(app_config)
        case _:
            raise RuntimeError(
                f"Unsupported usage buffer backend: {app_config.usage_buffer_backend}"
            )
