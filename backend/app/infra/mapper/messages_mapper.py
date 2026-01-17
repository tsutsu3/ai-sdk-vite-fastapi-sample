from datetime import datetime

from app.features.messages.models import MessagePartRecord, MessageRecord
from app.infra.model.messages_model import (
    FilePartDoc,
    ImagePartDoc,
    MessageDoc,
    MessagePartDoc,
    RagProgressPartDoc,
    RagSourcesPartDoc,
    TextPartDoc,
)


def _ensure_datetime(value: datetime | str | None) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    try:
        normalized = value.replace("Z", "+00:00") if value.endswith("Z") else value
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def record_part_to_doc(part: MessagePartRecord) -> MessagePartDoc:
    match part.type:
        case "text":
            return TextPartDoc(type="text", text=part.text or "")
        case "file":
            return FilePartDoc(type="file", file_id=part.file_id or "")
        case "image":
            return ImagePartDoc(type="image", file_id=part.image_id or "")
        case "rag-progress":
            return RagProgressPartDoc(type="rag-progress", text=part.text or "")
        case "rag-sources":
            return RagSourcesPartDoc(type="rag-sources", text=part.text or "")


def doc_part_to_record(part: MessagePartDoc) -> MessagePartRecord:
    match part.type:
        case "text":
            return MessagePartRecord(type="text", text=part.text)
        case "file":
            return MessagePartRecord(type="file", file_id=part.file_id)
        case "image":
            return MessagePartRecord(type="image", image_id=part.image_id)
        case "rag-progress":
            return MessagePartRecord(type="rag-progress", text=part.text)
        case "rag-sources":
            return MessagePartRecord(type="rag-sources", text=part.text)


def message_record_to_doc(
    record: MessageRecord,
    *,
    tenant_id: str,
    user_id: str,
    conversation_id: str,
    tool_id: str,
) -> MessageDoc:
    """Map repository message records to stored message documents."""
    payload = {
        "id": record.id,
        "tenant_id": tenant_id,
        "tool_id": tool_id,
        "user_id": user_id,
        "conversation_id": conversation_id,
        "role": record.role,
        "parent_message_id": record.parent_message_id or "",
        "parts": [record_part_to_doc(part) for part in record.parts],
        "model_id": record.model_id,
        "reaction": record.reaction,
    }
    if record.created_at:
        payload["created_at"] = record.created_at
    return MessageDoc(**payload)


def message_doc_to_record(doc: MessageDoc) -> MessageRecord:
    """Map stored message documents to repository message records."""
    return MessageRecord(
        id=doc.id,
        role=doc.role,
        parts=[doc_part_to_record(part) for part in doc.parts],
        created_at=_ensure_datetime(doc.created_at),
        parent_message_id=doc.parent_message_id,
        model_id=doc.model_id,
        reaction=doc.reaction,
    )
