from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class RetrievalMessage(BaseModel):
    """Chat message payload used for retrieval-style prompting."""

    model_config = ConfigDict(frozen=True)

    role: Literal["user", "assistant", "system"]
    content: str


class RetrievalQueryRequest(BaseModel):
    """Request payload for retrieval queries."""

    model_config = ConfigDict(populate_by_name=True, frozen=True)

    query: str
    data_source: str = Field(alias="dataSource")
    provider: str = "memory"
    tool_id: str | None = Field(default=None, alias="toolId")
    mode: Literal["retrievethenread", "chatreadretrieveread"] | None = None
    model: str | None = None
    messages: list[RetrievalMessage] = Field(default_factory=list)
    top_k: int = Field(default=5, alias="topK", ge=1, le=50)
    query_embedding: list[float] | None = Field(default=None, alias="queryEmbedding")


class RetrievalResult(BaseModel):
    """Single retrieval result item."""

    model_config = ConfigDict(frozen=True)

    text: str
    url: str
    title: str | None = None
    score: float | None = None


class RetrievalQueryResponse(BaseModel):
    """Response payload for retrieval queries."""

    model_config = ConfigDict(populate_by_name=True, frozen=True)

    provider: str
    data_source: str = Field(alias="dataSource")
    results: list[RetrievalResult]
