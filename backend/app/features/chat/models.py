from pydantic import BaseModel


class ChatRequest(BaseModel):
    model: str | None = None
