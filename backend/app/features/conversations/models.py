from pydantic import BaseModel


class ConversationMetadata(BaseModel, frozen=True):
    id: str
    title: str
    updatedAt: str
    createdAt: str | None = None


class ConversationsResponse(BaseModel, frozen=True):
    conversations: list[ConversationMetadata]


class ConversationResponse(BaseModel, frozen=True):
    id: str
    title: str
    messages: list[dict]
    updatedAt: str


class ConversationUpdateRequest(BaseModel):
    archived: bool | None = None
    title: str | None = None
