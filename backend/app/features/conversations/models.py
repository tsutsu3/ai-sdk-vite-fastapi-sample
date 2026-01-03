from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ConversationRecord(BaseModel):
    """Conversation metadata stored in the repository."""

    model_config = ConfigDict(frozen=True)

    id: str
    title: str
    toolId: str | None = None
    archived: bool = False
    updatedAt: datetime
    createdAt: datetime | None = None
