from pydantic import BaseModel


class MessagesResponse(BaseModel, frozen=True):
    messages: list[dict]
