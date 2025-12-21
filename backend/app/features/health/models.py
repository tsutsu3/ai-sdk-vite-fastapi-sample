from pydantic import BaseModel


class HealthResponse(BaseModel, frozen=True):
    status: str
