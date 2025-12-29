from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    """Health check response payload."""

    model_config = ConfigDict(frozen=True)

    status: str
