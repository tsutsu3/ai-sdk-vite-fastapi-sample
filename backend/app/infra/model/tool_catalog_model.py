from typing import Any
import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.features.retrieval.tools.registry import ProviderEnum, RetrievalToolModeEnum
from app.shared.time import now


class ToolPromptsDoc(BaseModel):
    """Tool prompts document representation."""

    model_config = ConfigDict(frozen=True)

    system: str = ""
    query: str | None = None
    hyde: str | None = None
    follow_up: str | None = None
    template: str | None = None
    chapter: str | None = None
    merge: str | None = None
    proofread: str | None = None


class ToolDoc(BaseModel):
    """Tool document representation."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    group_id: str
    group_label_key: str | None = None
    group_order: int | None = None
    label_key: str | None = None
    description_key: str | None = None
    data_source_id: str
    mode: RetrievalToolModeEnum = RetrievalToolModeEnum.SIMPLE
    top_k: int = 5
    enabled: bool = True
    get_extractive_answers: bool = False
    prompts: ToolPromptsDoc = Field(default_factory=ToolPromptsDoc)
    created_at: str = Field(default_factory=now)
    updated_at: str = Field(default_factory=now)


class DataSourceDoc(BaseModel):
    """Data source document representation."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    provider: ProviderEnum
    data_source: str
    config: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True
    created_at: str = Field(default_factory=now)
    updated_at: str = Field(default_factory=now)
