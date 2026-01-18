from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.features.retrieval.tools.registry import ProviderEnum, RetrievalToolModeEnum


class RetrievalMessage(BaseModel):
    """Chat message payload used for retrieval-style prompting."""

    model_config = ConfigDict(frozen=True)

    role: Literal["user", "assistant", "system"] = Field(
        description="Message role.",
        examples=["user"],
    )
    content: str = Field(
        description="Plain text content.",
        examples=["Summarize the onboarding steps."],
    )


class RetrievalQueryRequest(BaseModel):
    """Request payload for retrieval queries."""

    model_config = ConfigDict(
        populate_by_name=True,
        frozen=True,
        json_schema_extra={
            "examples": [
                {
                    "query": "Employee onboarding steps",
                    "dataSource": "tool01",
                    "provider": "memory",
                    "model": "gpt-4o",
                    "topK": 5,
                }
            ]
        },
    )

    query: str = Field(
        description="User query for retrieval.",
        examples=["Employee onboarding steps"],
    )
    pipeline: Literal["default", "longform"] = Field(
        default="default",
        description="Execution pipeline.",
    )
    chat_id: str | None = Field(
        default=None,
        alias="chatId",
        description="Conversation id (optional).",
    )
    data_source: str = Field(
        alias="dataSource",
        description="Data source identifier.",
        examples=["tool01"],
    )
    provider: ProviderEnum = Field(
        default=ProviderEnum.MEMORY,
        description="Retrieval provider.",
        examples=[ProviderEnum.MEMORY.value],
    )
    injected_prompt: str | None = Field(
        default=None,
        alias="injectedPrompt",
        description="Optional injected prompt for system templates.",
    )
    template_prompt: str | None = Field(
        default=None,
        alias="templatePrompt",
        description="Prompt for longform template generation.",
    )
    chapter_prompt: str | None = Field(
        default=None,
        alias="chapterPrompt",
        description="Prompt for longform chapter generation.",
    )
    merge_prompt: str | None = Field(
        default=None,
        alias="mergePrompt",
        description="Prompt for longform merge step.",
    )
    proofread_prompt: str | None = Field(
        default=None,
        alias="proofreadPrompt",
        description="Prompt for longform proofreading step.",
    )
    hyde_enabled: bool = Field(
        default=False,
        alias="hydeEnabled",
        description="Toggle HyDE query generation.",
    )
    tool_id: str | None = Field(
        default=None,
        alias="toolId",
        description="Retrieval tool id override.",
    )
    mode: RetrievalToolModeEnum | None = Field(
        default=None,
        description="Retrieval mode for response shaping.",
    )
    model: str | None = Field(
        default=None,
        description="Chat model id used for answer generation.",
        examples=["gpt-4o"],
    )
    messages: list[RetrievalMessage] = Field(
        default_factory=list,
        description="Conversation context for retrieval.",
    )
    top_k: int = Field(
        default=5,
        alias="topK",
        ge=1,
        le=50,
        description="Max number of results to return.",
    )
    chapter_count: int = Field(
        default=3,
        alias="chapterCount",
        ge=1,
        le=12,
        description="Number of chapters for longform output.",
    )
    chapter_titles: list[str] = Field(
        default_factory=list,
        alias="chapterTitles",
        description="Explicit chapter titles for longform output.",
    )
    query_embedding: list[float] | None = Field(
        default=None,
        alias="queryEmbedding",
        description="Optional precomputed embedding vector.",
    )


class RetrievalResult(BaseModel):
    """Single retrieval result item."""

    model_config = ConfigDict(frozen=True)

    text: str = Field(description="Snippet or content.")
    url: str = Field(description="Source URL or path.")
    title: str | None = Field(default=None, description="Source title.")
    score: float | None = Field(default=None, description="Relevance score.")


class RetrievalQueryResponse(BaseModel):
    """Response payload for retrieval queries."""

    model_config = ConfigDict(
        populate_by_name=True,
        frozen=True,
        json_schema_extra={
            "examples": [
                {
                    "provider": "memory",
                    "dataSource": "tool01",
                    "results": [
                        {
                            "text": "Onboarding steps include account setup and tool access.",
                            "url": "docs/onboarding.md",
                            "title": "Onboarding Guide",
                            "score": 0.92,
                        }
                    ],
                }
            ]
        },
    )

    provider: str = Field(description="Retrieval provider.")
    data_source: str = Field(alias="dataSource", description="Data source identifier.")
    results: list[RetrievalResult] = Field(description="Retrieval results.")
