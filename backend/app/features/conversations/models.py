from pydantic import BaseModel


class ConversationMetadata(BaseModel, frozen=True):
    id: str
    title: str
    updatedAt: str


class ConversationsResponse(BaseModel, frozen=True):
    conversations: list[ConversationMetadata]


class ConversationResponse(BaseModel, frozen=True):
    id: str
    title: str
    messages: list[dict]
    updatedAt: str