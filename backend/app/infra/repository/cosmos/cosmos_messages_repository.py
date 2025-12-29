from azure.cosmos.aio import ContainerProxy

from app.features.messages.models import MessageRecord
from app.features.messages.ports import MessageRepository
from app.infra.mapper.messages_mapper import (
    message_doc_to_record,
    message_record_to_doc,
)
from app.infra.model.messages_model import MessageDoc
from app.shared.time import now_datetime


def message_partition(tenant_id: str, conversation_id: str) -> str:
    """Build the Cosmos DB partition key for messages.

    Args:
        tenant_id: Tenant identifier.
        conversation_id: Conversation identifier.

    Returns:
        str: Partition key value.
    """
    return f"{tenant_id}/{conversation_id}"


class CosmosMessageRepository(MessageRepository):
    def __init__(self, container: ContainerProxy) -> None:
        self._container = container

    async def list_messages(
        self,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
        limit: int | None = None,
        continuation_token: str | None = None,
        descending: bool = False,
    ) -> tuple[list[MessageRecord], str | None]:
        pk = message_partition(tenant_id, conversation_id)
        order = "DESC" if descending else "ASC"
        query = (
            "SELECT * FROM c WHERE c.conversationId = @conversationId "
            "AND c.userId = @userId "
            f"ORDER BY c.createdAt {order}"
        )
        parameters = [
            {"name": "@conversationId", "value": conversation_id},
            {"name": "@userId", "value": user_id},
        ]
        results: list[MessageRecord] = []
        next_token: str | None = None
        if limit is None:
            items = self._container.query_items(
                query=query,
                parameters=parameters,
                partition_key=pk,
            )
            async for item in items:
                try:
                    results.append(message_doc_to_record(MessageDoc.model_validate(item)))
                except Exception:
                    continue
            return (results, None)
        items = self._container.query_items(
            query=query,
            parameters=parameters,
            partition_key=pk,
            max_item_count=limit,
        )
        page_iter = items.by_page(continuation_token=continuation_token)
        async for page in page_iter:
            async for item in page:
                try:
                    results.append(message_doc_to_record(MessageDoc.model_validate(item)))
                except Exception:
                    continue
            next_token = page_iter.continuation_token
            break
        return (results, next_token)

    async def upsert_messages(
        self,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
        messages: list[MessageRecord],
    ) -> list[MessageRecord]:
        # pk = message_partition(tenant_id, conversation_id)
        stored: list[MessageRecord] = []
        for message in messages:
            message_id = message.id
            if not message_id:
                continue
            created_at = message.created_at or now_datetime()
            parent_message_id = (
                message.parent_message_id if message.parent_message_id is not None else ""
            )
            if created_at != message.created_at or parent_message_id != message.parent_message_id:
                message = message.model_copy(
                    update={
                        "created_at": created_at,
                        "parent_message_id": parent_message_id,
                    }
                )
            item_doc = message_record_to_doc(
                message,
                tenant_id=tenant_id,
                user_id=user_id,
                conversation_id=conversation_id,
                tool_id="chat",
            )
            await self._container.upsert_item(
                item_doc.model_dump(by_alias=True, exclude_none=True)
            )
            stored.append(message)
        return stored

    async def delete_messages(self, tenant_id: str, user_id: str, conversation_id: str) -> None:
        pk = message_partition(tenant_id, conversation_id)
        items = self._container.query_items(
            query=(
                "SELECT c.id FROM c WHERE c.conversationId = @conversationId "
                "AND c.userId = @userId"
            ),
            parameters=[
                {"name": "@conversationId", "value": conversation_id},
                {"name": "@userId", "value": user_id},
            ],
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

    async def update_message_reaction(
        self,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
        message_id: str,
        reaction: str | None,
    ) -> MessageRecord | None:
        pk = message_partition(tenant_id, conversation_id)
        try:
            item = await self._container.read_item(item=message_id, partition_key=pk)
        except Exception:
            return None
        try:
            item_doc = MessageDoc.model_validate(item)
        except Exception:
            return None
        if item_doc.conversation_id != conversation_id or item_doc.user_id != user_id:
            return None
        updated_doc = item_doc.model_copy(update={"reaction": reaction})
        try:
            await self._container.replace_item(
                item=message_id,
                body=updated_doc.model_dump(by_alias=True, exclude_none=True),
            )
        except Exception:
            return None
        return message_doc_to_record(updated_doc)
