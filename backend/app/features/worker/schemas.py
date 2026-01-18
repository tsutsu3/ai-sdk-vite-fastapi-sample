from pydantic import BaseModel, Field

from app.features.authz.models import UserInfo
from app.features.retrieval.schemas import RetrievalQueryRequest


class WorkerJobRunRequest(BaseModel):
    """Payload for triggering a worker job."""

    job_id: str = Field(..., min_length=1)
    request: RetrievalQueryRequest
    user: UserInfo | None = None
