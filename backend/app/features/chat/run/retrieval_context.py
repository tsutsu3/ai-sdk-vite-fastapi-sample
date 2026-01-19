from dataclasses import dataclass

from langchain_core.prompts import PromptTemplate

from app.ai.models import RetrievalPolicy
from app.ai.ports import RetrieverBuilder
from app.ai.retrievers.factory import build_retriever_for_provider
from app.core.config import AppConfig
from app.features.authz.request_context import (
    get_current_membership,
    get_current_tenant_record,
    get_current_user_record,
)
from app.features.authz.tool_merge import merge_tools
from app.features.chat.run.errors import RunServiceError
from app.features.messages.models import MessageRecord
from app.features.retrieval.langchain_adapters import documents_to_results
from app.features.retrieval.schemas import RetrievalResult
from app.features.retrieval.tools import RetrievalToolSpec, ToolRegistry

MAX_RESULT_CHARS = 1000


@dataclass(frozen=True)
class RetrievalContextResult:
    tool: RetrievalToolSpec
    query: str
    results: list[RetrievalResult]
    system_message: str


def _is_authorized(tool_id: str, tools: list[str]) -> bool:
    return tool_id in tools


def _extract_user_query(messages: list[MessageRecord]) -> str:
    for message in reversed(messages):
        if message.role != "user":
            continue
        text_parts = [part.text or "" for part in message.parts if part.type == "text"]
        query = " ".join(part.strip() for part in text_parts if part).strip()
        if query:
            return query
    return ""


def _format_results(results: list[RetrievalResult], max_chars: int) -> str:
    lines: list[str] = []
    for index, result in enumerate(results, start=1):
        title = result.title or "Result"
        lines.append(f"{index}. {title}")
        lines.append(f"   URL: {result.url}")
        text = result.text.strip()
        if max_chars > 0 and len(text) > max_chars:
            text = text[: max_chars - 3].rstrip() + "..."
        if text:
            lines.append(f"   Content: {text}")
    return "\n".join(lines)


async def build_retrieval_context(
    *,
    tool_id: str | None,
    messages: list[MessageRecord],
    app_config: AppConfig,
    tenant_id: str,
    tool_registry: ToolRegistry,
    retriever_builder: RetrieverBuilder | None = None,
) -> RetrievalContextResult | None:
    """Build a retrieval context block for the requested tool."""
    tool = await tool_registry.resolve(tool_id, tenant_id)
    if not tool:
        if tool_id:
            raise RunServiceError(f"Unknown tool id: {tool_id}")
        return None

    user_record = get_current_user_record()
    tenant_record = get_current_tenant_record()
    membership = get_current_membership()
    if not user_record or not tenant_record or not membership:
        raise RunServiceError("User is not authorized for retrieval tools.")

    tools = merge_tools(
        tenant_record.default_tool_ids,
        membership.tool_overrides,
        available_tool_ids={tool.id},
    )
    if not _is_authorized(tool.id, tools):
        raise RunServiceError("Not authorized for the requested tool.")

    query = _extract_user_query(messages)
    if not query:
        return None

    top_k = max(1, min(tool.top_k, 20))
    provider_id = (tool.provider or "").strip().lower()
    if not provider_id:
        raise RunServiceError(f"Tool '{tool.id}' must define provider.")
    builder = retriever_builder or build_retriever_for_provider
    try:
        retriever = builder(
            app_config,
            provider_id=provider_id,
            data_source=tool.data_source,
            policy=RetrievalPolicy(k=top_k),
            tenant_id=tenant_id,
        )
    except RuntimeError as exc:
        raise RunServiceError(str(exc)) from exc
    documents = await retriever.ainvoke(query)
    results = documents_to_results(documents)
    formatted = _format_results(results, MAX_RESULT_CHARS)
    if formatted:
        prompt = PromptTemplate.from_template("{system_prompt}\n\nSources:\n{sources}")
        system_message = prompt.format(system_prompt=tool.system_prompt, sources=formatted)
    else:
        system_message = tool.system_prompt

    return RetrievalContextResult(
        tool=tool,
        query=query,
        results=results,
        system_message=system_message,
    )
