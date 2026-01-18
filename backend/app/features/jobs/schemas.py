from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.features.jobs.models import JobStatus
from app.features.worker.schemas import WorkerJobRunRequest


class JobStatusResponse(BaseModel):
    """Response schema for a single job status."""

    model_config = ConfigDict(populate_by_name=True, frozen=True)

    job_id: str = Field(alias="jobId")
    conversation_id: str | None = Field(default=None, alias="conversationId")
    status: JobStatus
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")


class JobStatusListResponse(BaseModel):
    """Response schema for job list."""

    model_config = ConfigDict(populate_by_name=True, frozen=True)

    items: list[JobStatusResponse]
    continuation_token: str | None = Field(default=None, alias="continuationToken")


class JobCreateResponse(BaseModel):
    """Response schema for job creation."""

    model_config = ConfigDict(populate_by_name=True, frozen=True)

    job_id: str = Field(alias="jobId")
    conversation_id: str = Field(alias="conversationId")
    worker_request: WorkerJobRunRequest = Field(alias="workerRequest")
