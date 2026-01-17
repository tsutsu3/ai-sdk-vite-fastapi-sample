from datetime import datetime

from azure.cosmos.aio import ContainerProxy

from app.features.conversations.models import ConversationRecord
from app.features.conversations.ports import ConversationRepository
from app.infra.mapper.conversations_mapper import (
    conversation_doc_to_record,
    conversation_record_to_doc,
)
from app.infra.model.conversations_model import ConversationDoc
from app.shared.constants import DEFAULT_CHAT_TITLE
from app.shared.time import now_datetime


def conversation_partition(tenant_id: str, user_id: str) -> str:
    """Build the Cosmos DB partition key for conversations.

    Args:
        tenant_id: Tenant identifier.
        user_id: User identifier.

    Returns:
        str: Partition key value.
    """
    return tenant_id


class CosmosConversationRepository(ConversationRepository):
    def __init__(self, container: ContainerProxy) -> None:
        self._container = container

    async def list_conversations(
        self,
        tenant_id: str,
        user_id: str,
        limit: int | None = None,
        continuation_token: str | None = None,
    ) -> tuple[list[ConversationRecord], str | None]:
        pk = conversation_partition(tenant_id, user_id)
        query = (
            "SELECT * FROM c WHERE c.userId = @userId AND "
            "(NOT IS_DEFINED(c.archived) OR c.archived = false) "
            "ORDER BY c.updatedAt DESC"
        )
        parameters = [{"name": "@userId", "value": user_id}]
        results: list[ConversationRecord] = []
        next_token: str | None = None
        if limit is None:
            items = self._container.query_items(
                query=query,
                parameters=parameters,
                partition_key=pk,
            )
            async for item in items:
                try:
                    doc = ConversationDoc.model_validate(item)
                except Exception:
                    continue
                results.append(conversation_doc_to_record(doc))
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
                    doc = ConversationDoc.model_validate(item)
                except Exception:
                    continue
                results.append(conversation_doc_to_record(doc))
            next_token = page_iter.continuation_token
            break
        return (results, next_token)

    async def list_archived_conversations(
        self,
        tenant_id: str,
        user_id: str,
        limit: int | None = None,
        continuation_token: str | None = None,
    ) -> tuple[list[ConversationRecord], str | None]:
        pk = conversation_partition(tenant_id, user_id)
        query = (
            "SELECT * FROM c WHERE c.userId = @userId AND "
            "IS_DEFINED(c.archived) AND c.archived = true "
            "ORDER BY c.updatedAt DESC"
        )
        parameters = [{"name": "@userId", "value": user_id}]
        results: list[ConversationRecord] = []
        next_token: str | None = None
        if limit is None:
            items = self._container.query_items(
                query=query,
                parameters=parameters,
                partition_key=pk,
            )
            async for item in items:
                try:
                    doc = ConversationDoc.model_validate(item)
                except Exception:
                    continue
                results.append(conversation_doc_to_record(doc))
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
                    doc = ConversationDoc.model_validate(item)
                except Exception:
                    continue
                results.append(conversation_doc_to_record(doc))
            next_token = page_iter.continuation_token
            break
        return (results, next_token)

    async def get_conversation(
        self,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
    ) -> ConversationRecord | None:
        pk = conversation_partition(tenant_id, user_id)
        try:
            item = await self._container.read_item(item=conversation_id, partition_key=pk)
        except Exception:
            return None
        try:
            doc = ConversationDoc.model_validate(item)
        except Exception:
            return None
        if doc.user_id != user_id:
            return None
        record = conversation_doc_to_record(doc)
        if not record.title:
            record = record.model_copy(update={"title": DEFAULT_CHAT_TITLE})
        return record

    async def upsert_conversation(
        self,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
        title: str,
        tool_id: str | None = None,
    ) -> ConversationRecord:
        pk = conversation_partition(tenant_id, user_id)
        updated_at = now_datetime()
        created_at = updated_at
        existing_tool_id = None
        try:
            existing = await self._container.read_item(item=conversation_id, partition_key=pk)
            try:
                existing_doc = ConversationDoc.model_validate(existing)
                if existing_doc.user_id == user_id:
                    created_at = existing_doc.created_at or created_at
                    existing_tool_id = existing_doc.tool_id
                else:
                    raw_created_at = existing.get("createdAt")
                    if isinstance(raw_created_at, str):
                        normalized = (
                            raw_created_at.replace("Z", "+00:00")
                            if raw_created_at.endswith("Z")
                            else raw_created_at
                        )
                        try:
                            created_at = datetime.fromisoformat(normalized)
                        except ValueError:
                            created_at = created_at
                    elif isinstance(raw_created_at, datetime):
                        created_at = raw_created_at
            except Exception:
                raw_created_at = existing.get("createdAt")
                if isinstance(raw_created_at, str):
                    normalized = (
                        raw_created_at.replace("Z", "+00:00")
                        if raw_created_at.endswith("Z")
                        else raw_created_at
                    )
                    try:
                        created_at = datetime.fromisoformat(normalized)
                    except ValueError:
                        created_at = created_at
                elif isinstance(raw_created_at, datetime):
                    created_at = raw_created_at
        except Exception:
            pass
        record = ConversationRecord(
            id=conversation_id,
            title=title or DEFAULT_CHAT_TITLE,
            toolId=tool_id or existing_tool_id or "chat",
            archived=False,
            updatedAt=updated_at,
            createdAt=created_at,
        )
        doc = conversation_record_to_doc(
            record,
            tenant_id=tenant_id,
            user_id=user_id,
            tool_id=record.toolId or "chat",
        )
        await self._container.upsert_item(doc.model_dump(by_alias=True, exclude_none=True))
        return record

    async def archive_conversation(
        self,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
        archived: bool,
    ) -> ConversationRecord | None:
        pk = conversation_partition(tenant_id, user_id)
        try:
            item = await self._container.read_item(item=conversation_id, partition_key=pk)
        except Exception:
            return None
        updated_at = now_datetime()
        try:
            doc = ConversationDoc.model_validate(item)
        except Exception:
            return None
        if doc.user_id != user_id:
            return None
        updated_doc = doc.model_copy(update={"archived": archived, "updated_at": updated_at})
        await self._container.replace_item(
            item=conversation_id,
            body=updated_doc.model_dump(by_alias=True, exclude_none=True),
        )
        record = conversation_doc_to_record(updated_doc)
        if not record.title:
            record = record.model_copy(update={"title": DEFAULT_CHAT_TITLE})
        return record

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
            query="SELECT c.id FROM c WHERE c.userId = @userId",
            parameters=[{"name": "@userId", "value": user_id}],
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
    ) -> ConversationRecord | None:
        pk = conversation_partition(tenant_id, user_id)
        try:
            item = await self._container.read_item(item=conversation_id, partition_key=pk)
        except Exception:
            return None
        updated_at = now_datetime()
        try:
            doc = ConversationDoc.model_validate(item)
        except Exception:
            return None
        if doc.user_id != user_id:
            return None
        updated_doc = doc.model_copy(update={"title": title, "updated_at": updated_at})
        await self._container.replace_item(
            item=conversation_id,
            body=updated_doc.model_dump(by_alias=True, exclude_none=True),
        )
        record = conversation_doc_to_record(updated_doc)
        if not record.title:
            record = record.model_copy(update={"title": DEFAULT_CHAT_TITLE})
        return record
