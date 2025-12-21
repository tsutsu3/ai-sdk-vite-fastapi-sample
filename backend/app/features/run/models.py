from pydantic import BaseModel


class RunRequest(BaseModel):
    id: str | None = None
    messages: list[dict] = []
    model: str | None = None
    webSearch: bool | None = None


class StreamContext(BaseModel):
    tenant_id: str
    user_id: str
    conversation_id: str

    message_id: str
    model_id: str | None

    title: str
    should_generate_title: bool

    messages: list[dict]
    openai_messages: list[dict]

    class Config:
        arbitrary_types_allowed = True
