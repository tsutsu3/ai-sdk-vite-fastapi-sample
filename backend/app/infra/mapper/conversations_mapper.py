from datetime import datetime

from app.features.conversations.models import ConversationRecord
from app.infra.model.conversations_model import ConversationDoc
from app.shared.constants import DEFAULT_CHAT_TITLE
from app.shared.time import now_datetime


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


def conversation_record_to_doc(
    record: ConversationRecord,
    *,
    tenant_id: str,
    user_id: str,
    tool_id: str,
) -> ConversationDoc:
    """Map repository conversation records to stored conversation documents."""
    payload = {
        "id": record.id,
        "tenant_id": tenant_id,
        "tool_id": record.toolId or tool_id,
        "user_id": user_id,
        "title": record.title,
        "archived": record.archived,
        "updated_at": record.updatedAt,
    }
    if record.createdAt:
        payload["created_at"] = record.createdAt
    return ConversationDoc(**payload)


def conversation_doc_to_record(doc: ConversationDoc) -> ConversationRecord:
    """Map stored conversation documents to repository conversation records."""
    return ConversationRecord(
        id=doc.id,
        title=doc.title or DEFAULT_CHAT_TITLE,
        toolId=doc.tool_id,
        archived=doc.archived,
        updatedAt=_ensure_datetime(doc.updated_at) or now_datetime(),
        createdAt=_ensure_datetime(doc.created_at),
    )
