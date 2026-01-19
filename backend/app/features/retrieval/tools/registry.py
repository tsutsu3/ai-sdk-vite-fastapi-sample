from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from app.features.tool_catalog.ports import ToolCatalogRepository


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


class ToolRegistry:
    """Scoped tool registry that resolves specs from the tool catalog."""

    def __init__(self, repo: ToolCatalogRepository) -> None:
        self._repo = repo

    async def resolve(self, tool_id: str | None, tenant_id: str) -> RetrievalToolSpec | None:
        """Resolve a retrieval tool spec by id for a tenant."""
        if not tool_id:
            return None
        normalized = tool_id.strip()
        if not normalized:
            return None
        tool = await self._repo.get_tool(tenant_id, normalized)
        if not tool or not tool.enabled:
            return None
        data_source = await self._repo.get_data_source(tenant_id, tool.data_source_id)
        if not data_source or not data_source.enabled:
            return None
        return RetrievalToolSpec(
            id=tool.id,
            data_source=data_source.data_source,
            system_prompt=tool.prompts.system,
            query_prompt=tool.prompts.query,
            hyde_prompt=tool.prompts.hyde,
            follow_up_questions_prompt=tool.prompts.follow_up,
            template_prompt=tool.prompts.template,
            chapter_prompt=tool.prompts.chapter,
            merge_prompt=tool.prompts.merge,
            proofread_prompt=tool.prompts.proofread,
            top_k=tool.top_k,
            provider=data_source.provider,
            mode=tool.mode,
            get_extractive_answers=tool.get_extractive_answers,
        )
