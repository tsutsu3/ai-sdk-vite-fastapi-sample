from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.shared.constants import DEFAULT_CHAT_TITLE
from app.shared.time import now_datetime


class ConversationDoc(BaseModel):
    """Stored conversation document representation."""

    model_config = ConfigDict(populate_by_name=True, frozen=True)

    id: str
    tenant_id: str = Field(alias="tenantId")
    tool_id: str = Field(alias="toolId")  # `chat` or tool id ( = tool name)
    user_id: str = Field(alias="userId")
    title: str = DEFAULT_CHAT_TITLE
    archived: bool = False
    version: int = 1  # To be used for future migrations
    created_at: datetime = Field(
        default_factory=now_datetime,
        alias="createdAt",
    )
    updated_at: datetime | None = Field(
        default=None,
        alias="updatedAt",
    )

    def model_post_init(self, __context):
        object.__setattr__(self, "updated_at", self.created_at)
