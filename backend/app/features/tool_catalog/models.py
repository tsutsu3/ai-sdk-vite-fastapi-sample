from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.features.retrieval.tools.registry import ProviderEnum, RetrievalToolModeEnum


class ToolPrompts(BaseModel):
    """Prompt payloads for a retrieval tool."""

    model_config = ConfigDict(frozen=True)

    system: str = ""
    query: str | None = None
    hyde: str | None = None
    follow_up: str | None = None
    template: str | None = None
    chapter: str | None = None
    merge: str | None = None
    proofread: str | None = None


class ToolRecord(BaseModel):
    """Tool metadata stored under a tenant."""

    model_config = ConfigDict(frozen=True)

    id: str
    tenant_id: str
    group_id: str
    group_label_key: str | None = None
    group_order: int | None = None
    label_key: str | None = None
    description_key: str | None = None
    data_source_id: str
    mode: RetrievalToolModeEnum = RetrievalToolModeEnum.SIMPLE
    top_k: int = Field(default=5, ge=1)
    enabled: bool = True
    get_extractive_answers: bool = False
    prompts: ToolPrompts = Field(default_factory=ToolPrompts)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class DataSourceRecord(BaseModel):
    """Data source configuration stored under a tenant."""

    model_config = ConfigDict(frozen=True)

    id: str
    tenant_id: str
    provider: ProviderEnum
    data_source: str
    config: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None
