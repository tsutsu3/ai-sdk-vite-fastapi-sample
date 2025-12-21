from datetime import datetime, timezone

from app.core.config import AppConfig
from app.features.usage.models import UsageRecord
from app.features.usage.ports import UsageRepository
from app.shared.infra.cosmos_client import get_cosmos_container


def current_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def usage_partition(tenant_id: str, user_id: str) -> str:
    return f"{tenant_id}/{user_id}"


class CosmosUsageRepository(UsageRepository):
    def __init__(self, config: AppConfig) -> None:
        self._container = get_cosmos_container(config, config.cosmos_usage_container)

    async def record_usage(self, record: UsageRecord) -> None:
        pk = usage_partition(record.tenant_id, record.user_id)
        doc = {
            "id": f"{record.conversation_id}:{record.message_id or 'usage'}",
            "tenantId": {"userId": pk},
            "conversationId": record.conversation_id,
            "messageId": record.message_id,
            "tokens": record.tokens,
            "createdAt": current_timestamp(),
        }
        await self._container.upsert_item(doc)
