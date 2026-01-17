from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ChatModelSpec(BaseModel):
    model_config = ConfigDict(frozen=True)

    provider: str
    model_id: str


class EmbeddingSpec(BaseModel):
    model_config = ConfigDict(frozen=True)

    provider: str
    model_id: str


class RetrieverSpec(BaseModel):
    model_config = ConfigDict(frozen=True)

    provider: str
    data_source: str
    embeddings: EmbeddingSpec | None = None


class HistoryKey(BaseModel):
    model_config = ConfigDict(frozen=True)

    tenant_id: str
    user_id: str
    conversation_id: str


class ModelPolicy(BaseModel):
    model_config = ConfigDict(frozen=True)

    primary: str
    fallbacks: list[str] = Field(default_factory=list)
    timeout_sec: int = 20


class RetrievalPolicy(BaseModel):
    model_config = ConfigDict(frozen=True)

    strategy: Literal["hybrid", "vector", "keyword"] = "hybrid"
    k: int = 10
    score_threshold: float | None = 0.3
    mmr: bool = False
    rerank: bool = True
    rag_mode: Literal["map_rerank", "stuff"] = "map_rerank"
    stuff_max_tokens: int = 1200
    get_extractive_answers: bool = False


class MemoryPolicy(BaseModel):
    model_config = ConfigDict(frozen=True)

    type: Literal["window", "summary", "buffer"] = "window"
    window_size: int = 16
    summary_update_every_turns: int = 6
    summary_prompt: str = "Summarize the conversation so far."


class RoutingPolicy(BaseModel):
    model_config = ConfigDict(frozen=True)

    tools: dict[str, str] = Field(default_factory=dict)


class DataSourcePolicy(BaseModel):
    model_config = ConfigDict(frozen=True)

    embeddings_id: str
    vector_index_id: str
    retrieval_policy_id: str = "default"


class Policies(BaseModel):
    model_config = ConfigDict(frozen=True)

    model_policy_chat: ModelPolicy
    model_policy_rag: ModelPolicy
    retrieval_policies: dict[str, RetrievalPolicy] = Field(default_factory=dict)
    memory_policy: MemoryPolicy = MemoryPolicy()
    routing_policy: RoutingPolicy = RoutingPolicy()
    data_sources: dict[str, DataSourcePolicy] = Field(default_factory=dict)
