from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.features.conversations.models import ConversationRecord
from app.features.messages.models import MessageRecord


class ConversationsResponse(BaseModel):
    """List response for conversation metadata."""

    model_config = ConfigDict(
        frozen=True,
        populate_by_name=True,
        json_schema_extra={
            "examples": [
                {
                    "conversations": [
                        {
                            "id": "conv-quickstart",
                            "title": "Project kickoff chat",
                            "toolId": "chat",
                            "archived": False,
                            "updatedAt": "2026-01-16T16:21:13.715Z",
                            "createdAt": "2026-01-16T16:21:13.715Z",
                        }
                    ],
                    "continuationToken": "0",
                }
            ]
        },
    )

    conversations: list[ConversationRecord] = Field(
        description="Conversation metadata list.",
    )
    continuation_token: str | None = Field(
        default=None,
        alias="continuationToken",
        description="Continuation token for paging.",
    )


class ConversationResponse(BaseModel):
    """Conversation response with messages."""

    model_config = ConfigDict(
        frozen=True,
        json_schema_extra={
            "examples": [
                {
                    "id": "conv-quickstart",
                    "title": "Project kickoff chat",
                    "toolId": "chat",
                    "archived": False,
                    "messages": [],
                    "updatedAt": "2026-01-16T16:21:13.715Z",
                }
            ]
        },
    )

    id: str = Field(description="Conversation id.")
    title: str = Field(description="Conversation title.")
    toolId: str | None = Field(default=None, description="Tool id associated with the chat.")
    archived: bool = Field(description="Archived flag.")
    messages: list[MessageRecord] = Field(description="Conversation messages.")
    updatedAt: datetime = Field(description="Last updated timestamp.")


class ConversationUpdateRequest(BaseModel):
    """Update payload for conversation changes."""

    model_config = ConfigDict(
        frozen=True,
        json_schema_extra={
            "examples": [
                {
                    "archived": True,
                },
            ]
        },
    )

    archived: bool | None = Field(
        default=None,
        description="Archive or unarchive the conversation.",
    )
    title: str | None = Field(
        default=None,
        description="New conversation title.",
    )
