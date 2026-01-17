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
    top_k: int = Field(default=5, ge=1)
    provider: ProviderEnum
    mode: RetrievalToolModeEnum = RetrievalToolModeEnum.SIMPLE
    get_extractive_answers: bool = False


DEFAULT_TOOL_SPECS: dict[str, RetrievalToolSpec] = {}
TOOL_SPECS: dict[str, RetrievalToolSpec] = {}

logger = logging.getLogger(__name__)


def initialize_tool_specs(config_path: str | None) -> None:
    """Load tool specs from YAML and store them in the registry."""
    if not config_path:
        TOOL_SPECS.clear()
        return
    path = Path(config_path)
    if not path.is_absolute() and not path.exists():
        candidate = Path(__file__).resolve().parents[4] / path
        if candidate.exists():
            path = candidate
        else:
            logger.debug(
                "retrieval.tools.config.missing path=%s fallback=%s",
                path,
                candidate,
            )
    tool_specs = _load_tool_specs_from_yaml(path)
    TOOL_SPECS.clear()
    TOOL_SPECS.update(tool_specs)


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


def resolve_tool(tool_id: str | None) -> RetrievalToolSpec | None:
    """Resolve a retrieval tool spec by id."""
    if not tool_id:
        return None

    specs = TOOL_SPECS or DEFAULT_TOOL_SPECS
    return specs.get(tool_id.strip())
