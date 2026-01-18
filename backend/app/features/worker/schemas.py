from pydantic import BaseModel, ConfigDict, Field

from app.features.authz.models import UserInfo
from app.features.retrieval.schemas import RetrievalQueryRequest


class WorkerJobRunRequest(BaseModel):
    """Payload for triggering a worker job."""

    model_config = ConfigDict(populate_by_name=True, frozen=True)

    job_id: str = Field(alias="jobId")
    request: RetrievalQueryRequest
    user: UserInfo | None = None
