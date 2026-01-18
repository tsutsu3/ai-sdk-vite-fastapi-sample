from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class JobStatus(str, Enum):
    """Job status values."""

    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"


class JobRecord(BaseModel):
    """Stored job record for longform execution."""

    model_config = ConfigDict(frozen=True)

    job_id: str = Field(description="Job id.")
    tenant_id: str = Field(description="Tenant id.")
    user_id: str = Field(description="User id.")
    conversation_id: str | None = Field(default=None, description="Conversation id.")
    status: JobStatus = Field(default=JobStatus.queued, description="Job status.")
    created_at: datetime = Field(description="Created timestamp.")
    updated_at: datetime = Field(description="Updated timestamp.")
