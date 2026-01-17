import base64
import json
from datetime import datetime
from logging import getLogger

from google.cloud import firestore

from app.features.conversations.models import ConversationRecord
from app.features.conversations.ports import ConversationRepository
from app.infra.mapper.conversations_mapper import (
    conversation_doc_to_record,
    conversation_record_to_doc,
)
from app.infra.model.conversations_model import ConversationDoc
from app.shared.constants import DEFAULT_CHAT_TITLE
from app.shared.time import now_datetime

logger = getLogger(__name__)


class FirestoreConversationRepository(ConversationRepository):
    def __init__(self, collection) -> None:
        self._collection = collection
        logger.info(
            "firestore.conversations.ready collection=%s",
            collection.id,
        )

    def _doc_id(self, tenant_id: str, user_id: str, conversation_id: str) -> str:
        return f"{tenant_id}:{user_id}:{conversation_id}"

    def _encode_cursor(self, updated_at: datetime, conversation_id: str) -> str:
        payload = {"updatedAt": updated_at.isoformat(), "id": conversation_id}
        raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
        return base64.urlsafe_b64encode(raw).decode("ascii")

    def _decode_cursor(self, token: str | None) -> tuple[datetime, str] | None:
        if not token:
            return None
        try:
            raw = base64.urlsafe_b64decode(token.encode("ascii"))
            payload = json.loads(raw.decode("utf-8"))
            updated_at = datetime.fromisoformat(payload["updatedAt"])
            conversation_id = str(payload["id"])
            return updated_at, conversation_id
        except Exception:
            logger.debug("firestore.conversations.invalid_cursor token=%s", token)
            return None

    async def list_conversations(
        self,
        tenant_id: str,
        user_id: str,
        limit: int | None = None,
        continuation_token: str | None = None,
    ) -> tuple[list[ConversationRecord], str | None]:
        logger.debug(
            "firestore.conversations.list tenant_id=%s user_id=%s limit=%s offset=%s",
            tenant_id,
            user_id,
            limit,
            continuation_token,
        )
        query = (
            self._collection.where("tenantId", "==", tenant_id)
            .where("userId", "==", user_id)
            .where("archived", "==", False)
            .order_by("updatedAt", direction=firestore.Query.DESCENDING)
            .order_by("id", direction=firestore.Query.DESCENDING)
        )
        cursor = self._decode_cursor(continuation_token)
        if cursor:
            query = query.start_after([cursor[0], cursor[1]])
        if limit is not None:
            query = query.limit(limit)
        results: list[ConversationRecord] = []
        async for doc in query.stream():
            try:
                item = ConversationDoc.model_validate(doc.to_dict())
            except Exception:
                continue
            results.append(conversation_doc_to_record(item))
        next_token = None
        if limit is not None and len(results) == limit:
            last = results[-1]
            last_updated = last.updatedAt or last.createdAt or now_datetime()
            next_token = self._encode_cursor(last_updated, last.id)
        return (results, next_token)

    async def list_archived_conversations(
        self,
        tenant_id: str,
        user_id: str,
        limit: int | None = None,
        continuation_token: str | None = None,
    ) -> tuple[list[ConversationRecord], str | None]:
        logger.debug(
            "firestore.conversations.list_archived tenant_id=%s user_id=%s limit=%s offset=%s",
            tenant_id,
            user_id,
            limit,
            continuation_token,
        )
        query = (
            self._collection.where("tenantId", "==", tenant_id)
            .where("userId", "==", user_id)
            .where("archived", "==", True)
            .order_by("updatedAt", direction=firestore.Query.DESCENDING)
            .order_by("id", direction=firestore.Query.DESCENDING)
        )
        cursor = self._decode_cursor(continuation_token)
        if cursor:
            query = query.start_after([cursor[0], cursor[1]])
        if limit is not None:
            query = query.limit(limit)
        results: list[ConversationRecord] = []
        async for doc in query.stream():
            try:
                item = ConversationDoc.model_validate(doc.to_dict())
            except Exception:
                continue
            results.append(conversation_doc_to_record(item))
        next_token = None
        if limit is not None and len(results) == limit:
            last = results[-1]
            last_updated = last.updatedAt or last.createdAt or now_datetime()
            next_token = self._encode_cursor(last_updated, last.id)
        return (results, next_token)

    async def get_conversation(
        self,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
    ) -> ConversationRecord | None:
        logger.debug(
            "firestore.conversations.get tenant_id=%s user_id=%s conversation_id=%s",
            tenant_id,
            user_id,
            conversation_id,
        )
        doc_id = self._doc_id(tenant_id, user_id, conversation_id)
        doc = await self._collection.document(doc_id).get()
        if not doc.exists:
            return None
        try:
            item = ConversationDoc.model_validate(doc.to_dict())
        except Exception:
            return None
        if item.user_id != user_id:
            return None
        record = conversation_doc_to_record(item)
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
        logger.debug(
            "firestore.conversations.upsert tenant_id=%s user_id=%s conversation_id=%s",
            tenant_id,
            user_id,
            conversation_id,
        )
        doc_id = self._doc_id(tenant_id, user_id, conversation_id)
        updated_at = now_datetime()
        created_at = updated_at
        existing_tool_id = None
        existing = await self._collection.document(doc_id).get()
        if existing.exists:
            try:
                existing_doc = ConversationDoc.model_validate(existing.to_dict())
                created_at = existing_doc.created_at or created_at
                existing_tool_id = existing_doc.tool_id
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
        await self._collection.document(doc_id).set(
            doc.model_dump(by_alias=True, exclude_none=True)
        )
        return record

    async def archive_conversation(
        self,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
        archived: bool,
    ) -> ConversationRecord | None:
        logger.debug(
            "firestore.conversations.archive tenant_id=%s user_id=%s conversation_id=%s archived=%s",
            tenant_id,
            user_id,
            conversation_id,
            archived,
        )
        doc_id = self._doc_id(tenant_id, user_id, conversation_id)
        doc_ref = self._collection.document(doc_id)
        doc = await doc_ref.get()
        if not doc.exists:
            return None
        try:
            item = ConversationDoc.model_validate(doc.to_dict())
        except Exception:
            return None
        if item.user_id != user_id:
            return None
        updated = item.model_copy(update={"archived": archived, "updated_at": now_datetime()})
        await doc_ref.set(updated.model_dump(by_alias=True, exclude_none=True))
        record = conversation_doc_to_record(updated)
        if not record.title:
            record = record.model_copy(update={"title": DEFAULT_CHAT_TITLE})
        return record

    async def delete_conversation(
        self,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
    ) -> bool:
        logger.debug(
            "firestore.conversations.delete tenant_id=%s user_id=%s conversation_id=%s",
            tenant_id,
            user_id,
            conversation_id,
        )
        doc_id = self._doc_id(tenant_id, user_id, conversation_id)
        doc_ref = self._collection.document(doc_id)
        doc = await doc_ref.get()
        if not doc.exists:
            return False
        await doc_ref.delete()
        return True

    async def update_title(
        self,
        tenant_id: str,
        user_id: str,
        conversation_id: str,
        title: str,
    ) -> ConversationRecord | None:
        logger.debug(
            "firestore.conversations.update_title tenant_id=%s user_id=%s conversation_id=%s",
            tenant_id,
            user_id,
            conversation_id,
        )
        doc_id = self._doc_id(tenant_id, user_id, conversation_id)
        doc_ref = self._collection.document(doc_id)
        doc = await doc_ref.get()
        if not doc.exists:
            return None
        try:
            item = ConversationDoc.model_validate(doc.to_dict())
        except Exception:
            return None
        if item.user_id != user_id:
            return None
        updated = item.model_copy(update={"title": title, "updated_at": now_datetime()})
        await doc_ref.set(updated.model_dump(by_alias=True, exclude_none=True))
        record = conversation_doc_to_record(updated)
        if not record.title:
            record = record.model_copy(update={"title": DEFAULT_CHAT_TITLE})
        return record

    async def list_all_conversation_ids(
        self,
        tenant_id: str,
        user_id: str,
    ) -> list[str]:
        logger.debug(
            "firestore.conversations.list_all tenant_id=%s user_id=%s",
            tenant_id,
            user_id,
        )
        query = self._collection.where("tenantId", "==", tenant_id).where("userId", "==", user_id)
        results: list[str] = []
        async for doc in query.stream():
            item = doc.to_dict() or {}
            conv_id = item.get("id")
            if isinstance(conv_id, str):
                results.append(conv_id)
        return results
