from __future__ import annotations

from logging import getLogger

from google.cloud import firestore

from app.features.messages.models import MessageRecord
from app.features.messages.ports import MessageRepository
from app.infra.mapper.messages_mapper import (
    message_doc_to_record,
    message_record_to_doc,
)
from app.infra.model.messages_model import MessageDoc
from app.shared.time import now_datetime

logger = getLogger(__name__)


class FirestoreMessageRepository(MessageRepository):
    def __init__(self, client: firestore.AsyncClient, *, config) -> None:
        self._client = client
        self._collection = client.collection(config.cosmos_messages_container)
        logger.info(
            "firestore.messages.ready collection=%s",
            config.cosmos_messages_container,
        )

    def _doc_id(self, tenant_id: str, user_id: str, conversation_id: str, message_id: str) -> str:
        return f"{tenant_id}:{user_id}:{conversation_id}:{message_id}"

    async def list_messages(
        self,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
        limit: int | None = None,
        continuation_token: str | None = None,
        descending: bool = False,
    ) -> tuple[list[MessageRecord], str | None]:
        logger.debug(
            "firestore.messages.list tenant_id=%s user_id=%s conversation_id=%s limit=%s offset=%s descending=%s",
            tenant_id,
            user_id,
            conversation_id,
            limit,
            continuation_token,
            descending,
        )
        direction = firestore.Query.DESCENDING if descending else firestore.Query.ASCENDING
        query = (
            self._collection.where("tenantId", "==", tenant_id)
            .where("userId", "==", user_id)
            .where("conversationId", "==", conversation_id)
            .order_by("createdAt", direction=direction)
        )
        offset = int(continuation_token) if continuation_token else 0
        if limit is not None:
            query = query.offset(offset).limit(limit)
        results: list[MessageRecord] = []
        async for doc in query.stream():
            try:
                item = MessageDoc.model_validate(doc.to_dict())
            except Exception:
                continue
            results.append(message_doc_to_record(item))
        next_token = None
        if limit is not None and len(results) == limit:
            next_token = str(offset + len(results))
        return (results, next_token)

    async def upsert_messages(
        self,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
        messages: list[MessageRecord],
    ) -> list[MessageRecord]:
        logger.debug(
            "firestore.messages.upsert tenant_id=%s user_id=%s conversation_id=%s count=%s",
            tenant_id,
            user_id,
            conversation_id,
            len(messages),
        )
        for message in messages:
            doc_id = self._doc_id(tenant_id, user_id, conversation_id, message.id)
            doc_ref = self._collection.document(doc_id)
            existing = await doc_ref.get()
            if existing.exists:
                try:
                    existing_doc = MessageDoc.model_validate(existing.to_dict())
                    created_at = message.created_at or existing_doc.created_at
                    parent_message_id = (
                        message.parent_message_id
                        if message.parent_message_id is not None
                        else existing_doc.parent_message_id
                    )
                except Exception:
                    created_at = message.created_at or now_datetime()
                    parent_message_id = message.parent_message_id or ""
            else:
                created_at = message.created_at or now_datetime()
                parent_message_id = message.parent_message_id or ""

            if created_at != message.created_at or parent_message_id != message.parent_message_id:
                message = message.model_copy(
                    update={
                        "created_at": created_at,
                        "parent_message_id": parent_message_id,
                    }
                )
            doc = message_record_to_doc(
                message,
                tenant_id=tenant_id,
                user_id=user_id,
                conversation_id=conversation_id,
                tool_id="chat",
            )
            await doc_ref.set(doc.model_dump(by_alias=True, exclude_none=True, mode="json"))
        return list(messages)

    async def delete_messages(self, tenant_id: str, user_id: str, conversation_id: str) -> None:
        logger.debug(
            "firestore.messages.delete tenant_id=%s user_id=%s conversation_id=%s",
            tenant_id,
            user_id,
            conversation_id,
        )
        query = (
            self._collection.where("tenantId", "==", tenant_id)
            .where("userId", "==", user_id)
            .where("conversationId", "==", conversation_id)
        )
        async for doc in query.stream():
            await doc.reference.delete()

    async def update_message_reaction(
        self,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
        message_id: str,
        reaction: str | None,
    ) -> MessageRecord | None:
        logger.debug(
            "firestore.messages.update_reaction tenant_id=%s user_id=%s conversation_id=%s message_id=%s reaction=%s",
            tenant_id,
            user_id,
            conversation_id,
            message_id,
            reaction,
        )
        doc_id = self._doc_id(tenant_id, user_id, conversation_id, message_id)
        doc_ref = self._collection.document(doc_id)
        existing = await doc_ref.get()
        if not existing.exists:
            return None
        try:
            item = MessageDoc.model_validate(existing.to_dict())
        except Exception:
            return None
        updated = item.model_copy(update={"reaction": reaction})
        await doc_ref.set(updated.model_dump(by_alias=True, exclude_none=True, mode="json"))
        return message_doc_to_record(updated)
