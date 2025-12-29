from pydantic import BaseModel, ConfigDict, Field


class RetrievalQueryRequest(BaseModel):
    """Request payload for retrieval queries."""

    model_config = ConfigDict(populate_by_name=True, frozen=True)

    query: str
    data_source: str = Field(alias="dataSource")
    provider: str = "memory"
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
