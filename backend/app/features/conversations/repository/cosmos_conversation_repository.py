from datetime import datetime, timezone

from app.core.config import AppConfig
from app.features.conversations.models import ConversationMetadata
from app.features.conversations.ports import ConversationRepository
from app.shared.constants import DEFAULT_CHAT_TITLE
from app.shared.infra.cosmos_client import get_cosmos_container


def current_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def conversation_partition(tenant_id: str, user_id: str) -> str:
    return f"{tenant_id}/{user_id}"


class CosmosConversationRepository(ConversationRepository):
    def __init__(self, config: AppConfig) -> None:
        self._container = get_cosmos_container(config, config.cosmos_conversations_container)

    async def list_conversations(
        self,
        tenant_id: str,
        user_id: str,
    ) -> list[ConversationMetadata]:
        pk = conversation_partition(tenant_id, user_id)
        items = self._container.query_items(
            query=(
                "SELECT * FROM c WHERE "
                "(NOT IS_DEFINED(c.archived) OR c.archived = false) "
                "ORDER BY c.updatedAt DESC"
            ),
            partition_key=pk,
        )
        results = []
        async for item in items:
            results.append(item)
        return [
            ConversationMetadata(
                id=item["id"],
                title=item.get("title") or DEFAULT_CHAT_TITLE,
                updatedAt=item.get("updatedAt") or current_timestamp(),
                createdAt=item.get("createdAt"),
            )
            for item in results
        ]

    async def list_archived_conversations(
        self,
        tenant_id: str,
        user_id: str,
    ) -> list[ConversationMetadata]:
        pk = conversation_partition(tenant_id, user_id)
        items = self._container.query_items(
            query=(
                "SELECT * FROM c WHERE "
                "IS_DEFINED(c.archived) AND c.archived = true "
                "ORDER BY c.updatedAt DESC"
            ),
            partition_key=pk,
        )
        results = []
        async for item in items:
            results.append(item)
        return [
            ConversationMetadata(
                id=item["id"],
                title=item.get("title") or DEFAULT_CHAT_TITLE,
                updatedAt=item.get("updatedAt") or current_timestamp(),
                createdAt=item.get("createdAt"),
            )
            for item in results
        ]

    async def get_conversation(
        self,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
    ) -> ConversationMetadata | None:
        pk = conversation_partition(tenant_id, user_id)
        try:
            item = await self._container.read_item(item=conversation_id, partition_key=pk)
        except Exception:
            return None
        return ConversationMetadata(
            id=item["id"],
            title=item.get("title") or DEFAULT_CHAT_TITLE,
            updatedAt=item.get("updatedAt") or current_timestamp(),
            createdAt=item.get("createdAt"),
        )

    async def upsert_conversation(
        self,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
        title: str,
        updated_at: str,
    ) -> ConversationMetadata:
        pk = conversation_partition(tenant_id, user_id)
        created_at = updated_at
        try:
            existing = await self._container.read_item(item=conversation_id, partition_key=pk)
            created_at = existing.get("createdAt") or created_at
        except Exception:
            pass
        doc = {
            "id": conversation_id,
            "tenantId": {"userId": pk},
            "userId": user_id,
            "title": title,
            "updatedAt": updated_at,
            "createdAt": created_at,
            "archived": False,
        }
        await self._container.upsert_item(doc)
        return ConversationMetadata(
            id=conversation_id,
            title=title,
            updatedAt=updated_at,
            createdAt=created_at,
        )

    async def archive_conversation(
        self,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
        archived: bool,
        updated_at: str,
    ) -> ConversationMetadata | None:
        pk = conversation_partition(tenant_id, user_id)
        try:
            item = await self._container.read_item(item=conversation_id, partition_key=pk)
        except Exception:
            return None
        item["archived"] = archived
        item["updatedAt"] = updated_at
        await self._container.replace_item(item=conversation_id, body=item)
        return ConversationMetadata(
            id=item["id"],
            title=item.get("title") or DEFAULT_CHAT_TITLE,
            updatedAt=item.get("updatedAt") or current_timestamp(),
            createdAt=item.get("createdAt"),
        )

    async def delete_conversation(
        self,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
    ) -> bool:
        pk = conversation_partition(tenant_id, user_id)
        try:
            await self._container.delete_item(item=conversation_id, partition_key=pk)
        except Exception:
            return False
        return True

    async def list_all_conversation_ids(
        self,
        tenant_id: str,
        user_id: str,
    ) -> list[str]:
        pk = conversation_partition(tenant_id, user_id)
        items = self._container.query_items(
            query="SELECT c.id FROM c",
            partition_key=pk,
        )
        results = []
        async for item in items:
            if item.get("id"):
                results.append(item.get("id"))
        return results

    async def update_title(
        self,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
        title: str,
        updated_at: str,
    ) -> ConversationMetadata | None:
        pk = conversation_partition(tenant_id, user_id)
        try:
            item = await self._container.read_item(item=conversation_id, partition_key=pk)
        except Exception:
            return None
        item["title"] = title
        item["updatedAt"] = updated_at
        await self._container.replace_item(item=conversation_id, body=item)
        return ConversationMetadata(
            id=item["id"],
            title=item.get("title") or DEFAULT_CHAT_TITLE,
            updatedAt=item.get("updatedAt") or current_timestamp(),
            createdAt=item.get("createdAt"),
        )
