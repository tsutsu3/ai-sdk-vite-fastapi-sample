from pydantic import BaseModel

from app.features.messages.models import ChatMessage


class ConversationMetadata(BaseModel, frozen=True):
    id: str
    title: str
    archived: bool = False
    updatedAt: str
    createdAt: str | None = None


class ConversationsResponse(BaseModel, frozen=True):
    conversations: list[ConversationMetadata]


class ConversationResponse(BaseModel, frozen=True):
    id: str
    title: str
    messages: list[ChatMessage]
    updatedAt: str


class ConversationUpdateRequest(BaseModel):
    archived: bool | None = None
    title: str | None = None
