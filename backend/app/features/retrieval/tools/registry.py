import logging
from enum import Enum
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field


class ProviderEnum(str, Enum):
    MEMORY = "memory"
    LOCAL_FILES = "local-files"
    AI_SEARCH = "ai-search"
    VERTEX_SEARCH = "vertex-search"
    VERTEX_ANSWER = "vertex-answer"


class RetrievalToolModeEnum(str, Enum):
    SIMPLE = "simple"  #
    CHAT = "chat"
    ANSWER = "answer"  # vertex ai searh + answer


class RetrievalToolSpec(BaseModel):
    """Static configuration for a retrieval tool."""

    model_config = ConfigDict(frozen=True)

    id: str
    data_source: str
    system_prompt: str
    query_prompt: str | None = None
    hyde_prompt: str | None = None
    follow_up_questions_prompt: str | None = None
    template_prompt: str | None = None
    chapter_prompt: str | None = None
    merge_prompt: str | None = None
    proofread_prompt: str | None = None
    top_k: int = Field(default=5, ge=1)
    provider: ProviderEnum
    mode: RetrievalToolModeEnum = RetrievalToolModeEnum.SIMPLE
    get_extractive_answers: bool = False


logger = logging.getLogger(__name__)

class ToolRegistry:
    """Scoped tool registry to avoid cross-tenant shared state."""

    def __init__(self) -> None:
        self._default_specs: dict[str, RetrievalToolSpec] = {}
        self._tenant_specs: dict[str, dict[str, RetrievalToolSpec]] = {}

    def load_default_specs(self, config_path: str | None) -> None:
        """Load default tool specs from YAML."""
        if not config_path:
            self._default_specs.clear()
            return
        path = _resolve_tool_config_path(config_path)
        tool_specs = _load_tool_specs_from_yaml(path)
        self._default_specs = tool_specs

    def load_tenant_specs(self, tenant_id: str, config_path: str | None) -> None:
        """Load tenant-specific tool specs from YAML."""
        if not config_path:
            self._tenant_specs.pop(tenant_id, None)
            return
        path = _resolve_tool_config_path(config_path)
        tool_specs = _load_tool_specs_from_yaml(path)
        self._tenant_specs[tenant_id] = tool_specs

    def resolve(self, tool_id: str | None, tenant_id: str) -> RetrievalToolSpec | None:
        """Resolve a retrieval tool spec by id for a tenant."""
        if not tool_id:
            return None
        normalized = tool_id.strip()
        if not normalized:
            return None
        specs = self._tenant_specs.get(tenant_id) or self._default_specs
        return specs.get(normalized)


def initialize_tool_specs(registry: ToolRegistry, config_path: str | None) -> None:
    """Load tool specs from YAML into the provided registry."""
    registry.load_default_specs(config_path)


def _resolve_tool_config_path(config_path: str) -> Path:
    path = Path(config_path)
    if not path.is_absolute() and not path.exists():
        candidate = Path(__file__).resolve().parents[4] / path
        if candidate.exists():
            return candidate
        logger.debug(
            "retrieval.tools.config.missing path=%s fallback=%s",
            path,
            candidate,
        )
    return path


def _load_tool_specs_from_yaml(path: Path) -> dict[str, RetrievalToolSpec]:
    if not path.exists():
        raise FileNotFoundError(f"Retrieval tool config not found: {path}")

    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    if isinstance(raw, dict) and "tools" in raw:
        raw = raw["tools"]

    if not isinstance(raw, dict):
        raise ValueError("Retrieval tool config must be a mapping of tool ids to specs.")

    specs: dict[str, RetrievalToolSpec] = {}
    for tool_id, payload in raw.items():
        if not isinstance(payload, dict):
            raise ValueError(f"Tool '{tool_id}' must be a mapping of fields.")

        data: dict[str, Any] = dict(payload)
        data.setdefault("id", tool_id)
        data.setdefault("data_source", tool_id)
        spec = RetrievalToolSpec.model_validate(data)

        if not (spec.provider or "").strip():
            raise ValueError(f"Tool '{spec.id}' must define provider.")

        specs[spec.id] = spec

    return specs
