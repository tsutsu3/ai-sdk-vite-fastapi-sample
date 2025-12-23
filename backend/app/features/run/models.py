from pydantic import BaseModel, ConfigDict, Field

from app.features.messages.models import ChatMessage


class OpenAIMessage(BaseModel):
    model_config = ConfigDict(extra="allow")

    role: str
    content: str


class RunRequest(BaseModel):
    id: str | None = None
    messages: list[ChatMessage] = []
    model: str | None = None
    webSearch: bool | None = None


class WebSearchRequest(BaseModel):
    enabled: bool = False
    engine: str | None = None


class StreamContext(BaseModel):
    tenant_id: str
    user_id: str
    conversation_id: str

    message_id: str
    model_id: str | None

    title: str
    should_generate_title: bool

    messages: list[ChatMessage]
    openai_messages: list[OpenAIMessage]
    web_search: WebSearchRequest = Field(default_factory=WebSearchRequest)

    class Config:
        arbitrary_types_allowed = True
