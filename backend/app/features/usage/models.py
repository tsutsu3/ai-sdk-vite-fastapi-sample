from pydantic import BaseModel, ConfigDict


class UsageRecord(BaseModel):
    """Usage record for a chat interaction."""

    model_config = ConfigDict(frozen=True)

    tenant_id: str
    user_id: str
    conversation_id: str
    message_id: str | None = None
    model_id: str | None = None
    tokens_in: int | None = None
    tokens_out: int | None = None
    bytes_in: int | None = None
    bytes_out: int | None = None
    requests: int = 1
