from __future__ import annotations

from dataclasses import dataclass

from app.features.authz.request_context import (
    get_current_tenant_record,
    get_current_user_record,
)
from app.features.authz.tool_merge import merge_tools
from app.features.messages.models import MessageRecord
from app.features.retrieval.schemas import RetrievalResult
from app.features.retrieval.service import RetrievalService
from app.features.retrieval.tools import RetrievalToolSpec, resolve_tool
from app.features.run.errors import RunServiceError


@dataclass(frozen=True)
class RetrievalContextResult:
    tool: RetrievalToolSpec
    query: str
    results: list[RetrievalResult]
    system_message: str


def _is_authorized(tool_id: str, tools: list[str]) -> bool:
    for tool in tools:
        if tool_id == tool or tool_id.startswith(tool):
            return True
    return False


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
    retrieval_service: RetrievalService,
) -> RetrievalContextResult | None:
    """Build a retrieval context block for the requested tool."""
    tool = resolve_tool(tool_id)
    if not tool:
        if tool_id:
            raise RunServiceError(f"Unknown tool id: {tool_id}")
        return None

    user_record = get_current_user_record()
    tenant_record = get_current_tenant_record()
    if not user_record or not tenant_record:
        raise RunServiceError("User is not authorized for retrieval tools.")

    tools = merge_tools(tenant_record.default_tools, user_record.tool_overrides)
    if not _is_authorized(tool.id, tools):
        raise RunServiceError("Not authorized for the requested tool.")

    query = _extract_user_query(messages)
    if not query:
        return None

    top_k = max(1, min(tool.top_k, 20))
    results = list(
        await retrieval_service.search(
            query,
            tool.data_source,
            tool.provider,
            top_k=top_k,
        )
    )
    formatted = _format_results(results, tool.max_result_chars)
    if formatted:
        system_message = f"{tool.system_prompt}\n\nSources:\n{formatted}"
    else:
        system_message = tool.system_prompt

    return RetrievalContextResult(
        tool=tool,
        query=query,
        results=results,
        system_message=system_message,
    )
