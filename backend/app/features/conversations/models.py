from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ConversationRecord(BaseModel):
    """Conversation metadata stored in the repository."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(description="Conversation id.", examples=["conv-quickstart"])
    title: str = Field(description="Conversation title.", examples=["Project kickoff chat"])
    toolId: str | None = Field(
        default=None,
        description="Tool id associated with the chat.",
        examples=["chat"],
    )
    archived: bool = Field(default=False, description="Archived flag.", examples=[False])
    updatedAt: datetime = Field(
        description="Last updated timestamp.",
        examples=["2026-01-16T16:21:13.715Z"],
    )
    createdAt: datetime | None = Field(
        default=None,
        description="Created timestamp.",
        examples=["2026-01-16T16:21:13.715Z"],
    )
