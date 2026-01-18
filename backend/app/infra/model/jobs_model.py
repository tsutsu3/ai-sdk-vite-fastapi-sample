from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.features.jobs.models import JobStatus
from app.shared.time import now_datetime


class JobDoc(BaseModel):
    """Stored job document representation."""

    model_config = ConfigDict(populate_by_name=True, frozen=True)

    id: str
    tenant_id: str = Field(alias="tenantId")
    user_id: str = Field(alias="userId")
    conversation_id: str | None = Field(default=None, alias="conversationId")
    status: JobStatus = Field(default=JobStatus.queued)
    created_at: datetime = Field(default_factory=now_datetime, alias="createdAt")
    updated_at: datetime | None = Field(default=None, alias="updatedAt")

    def model_post_init(self, __context):
        object.__setattr__(self, "updated_at", self.created_at)
