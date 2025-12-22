from datetime import datetime, timezone
from typing import Any

from app.core.config import AppConfig
from app.features.messages.models import ChatMessage
from app.features.messages.ports import MessageRepository
from app.shared.infra.cosmos_client import get_cosmos_container


def current_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def message_partition(tenant_id: str, conversation_id: str) -> str:
    return f"{tenant_id}/{conversation_id}"


class CosmosMessageRepository(MessageRepository):
    def __init__(self, config: AppConfig) -> None:
        self._container = get_cosmos_container(config, config.cosmos_messages_container)

    async def list_messages(self, tenant_id: str, conversation_id: str) -> list[ChatMessage]:
        pk = message_partition(tenant_id, conversation_id)
        query = (
            "SELECT * FROM c WHERE c.conversationId = @conversationId " "ORDER BY c.createdAt ASC"
        )
        items = self._container.query_items(
            query=query,
            parameters=[{"name": "@conversationId", "value": conversation_id}],
            partition_key=pk,
        )
        results = []
        async for item in items:
            message = item.get("message")
            if not isinstance(message, dict):
                continue
            try:
                results.append(ChatMessage.model_validate(message))
            except Exception:
                continue
        return results

    async def upsert_messages(
        self,
        tenant_id: str,
        conversation_id: str,
        messages: list[ChatMessage],
    ) -> None:
        pk = message_partition(tenant_id, conversation_id)
        for message in messages:
            message_id = message.id
            if not message_id:
                continue
            doc: dict[str, Any] = {
                "id": str(message_id),
                "tenantId": {"convId": pk},
                "conversationId": conversation_id,
                "message": message.model_dump(by_alias=True, exclude_none=True),
                "createdAt": current_timestamp(),
            }
            await self._container.upsert_item(doc)

    async def delete_messages(self, tenant_id: str, conversation_id: str) -> None:
        pk = message_partition(tenant_id, conversation_id)
        items = self._container.query_items(
            query="SELECT c.id FROM c WHERE c.conversationId = @conversationId",
            parameters=[{"name": "@conversationId", "value": conversation_id}],
            partition_key=pk,
        )
        async for item in items:
            message_id = item.get("id")
            if not message_id:
                continue
            try:
                await self._container.delete_item(item=message_id, partition_key=pk)
            except Exception:
                continue
