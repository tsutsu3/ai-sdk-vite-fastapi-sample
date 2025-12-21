from pydantic import BaseModel


class UsageRecord(BaseModel, frozen=True):
    tenant_id: str
    user_id: str
    conversation_id: str
    message_id: str | None = None
    tokens: int | None = None
