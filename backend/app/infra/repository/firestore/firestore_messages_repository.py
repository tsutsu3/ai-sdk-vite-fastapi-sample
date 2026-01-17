import asyncio
import base64
import json
from datetime import datetime
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
    def __init__(self, collection) -> None:
        self._collection = collection
        logger.info(
            "firestore.messages.ready collection=%s",
            collection.id,
        )

    def _doc_id(self, tenant_id: str, user_id: str, conversation_id: str, message_id: str) -> str:
        return f"{tenant_id}:{user_id}:{conversation_id}:{message_id}"

    def _encode_cursor(self, created_at: datetime, message_id: str) -> str:
        payload = {"createdAt": created_at.isoformat(), "id": message_id}
        raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
        return base64.urlsafe_b64encode(raw).decode("ascii")

    def _decode_cursor(self, token: str | None) -> tuple[datetime, str] | None:
        if not token:
            return None
        try:
            raw = base64.urlsafe_b64decode(token.encode("ascii"))
            payload = json.loads(raw.decode("utf-8"))
            created_at = datetime.fromisoformat(payload["createdAt"])
            message_id = str(payload["id"])
            return created_at, message_id
        except Exception:
            logger.debug("firestore.messages.invalid_cursor token=%s", token)
            return None

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
            .order_by("id", direction=direction)
        )
        cursor = self._decode_cursor(continuation_token)
        if cursor:
            query = query.start_after([cursor[0], cursor[1]])
        if limit is not None:
            query = query.limit(limit)
        results: list[MessageRecord] = []
        async for doc in query.stream():
            try:
                item = MessageDoc.model_validate(doc.to_dict())
            except Exception:
                continue
            results.append(message_doc_to_record(item))
        next_token = None
        if limit is not None and len(results) == limit:
            last = results[-1]
            last_created = last.created_at or now_datetime()
            next_token = self._encode_cursor(last_created, last.id)
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
        if not messages:
            return []

        needs_fetch: list[tuple[MessageRecord, firestore.AsyncDocumentReference]] = []
        for message in messages:
            if message.created_at is None or message.parent_message_id is None:
                doc_id = self._doc_id(tenant_id, user_id, conversation_id, message.id)
                needs_fetch.append((message, self._collection.document(doc_id)))

        if needs_fetch:
            fetch_tasks = [ref.get() for _, ref in needs_fetch]
            fetch_results = await asyncio.gather(*fetch_tasks, return_exceptions=True)
        else:
            fetch_results = []

        resolved: dict[str, MessageRecord] = {}
        for (message, _), result in zip(needs_fetch, fetch_results):
            created_at = message.created_at
            parent_message_id = message.parent_message_id
            if isinstance(result, Exception):
                created_at = created_at or now_datetime()
                parent_message_id = parent_message_id or ""
            else:
                try:
                    if result.exists:
                        existing_doc = MessageDoc.model_validate(result.to_dict())
                        created_at = created_at or existing_doc.created_at
                        if parent_message_id is None:
                            parent_message_id = existing_doc.parent_message_id
                except Exception:
                    created_at = created_at or now_datetime()
                    parent_message_id = parent_message_id or ""
            if created_at is None:
                created_at = now_datetime()
            if parent_message_id is None:
                parent_message_id = ""
            if created_at != message.created_at or parent_message_id != message.parent_message_id:
                message = message.model_copy(
                    update={
                        "created_at": created_at,
                        "parent_message_id": parent_message_id,
                    }
                )
            resolved[message.id] = message

        batch = self._client.batch()
        for message in messages:
            if message.id in resolved:
                message = resolved[message.id]
            doc_id = self._doc_id(tenant_id, user_id, conversation_id, message.id)
            doc_ref = self._collection.document(doc_id)
            doc = message_record_to_doc(
                message,
                tenant_id=tenant_id,
                user_id=user_id,
                conversation_id=conversation_id,
                tool_id="chat",
            )
            batch.set(doc_ref, doc.model_dump(by_alias=True, exclude_none=True, mode="json"))

        await batch.commit()
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
        batch = self._client.batch()
        batch_count = 0
        async for doc in query.stream():
            batch.delete(doc.reference)
            batch_count += 1
            if batch_count >= 450:
                await batch.commit()
                batch = self._client.batch()
                batch_count = 0
        if batch_count:
            await batch.commit()

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
