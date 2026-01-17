import json
from typing import Any

from langchain_core.messages import AIMessageChunk, BaseMessage
from langchain_core.prompts import PromptTemplate

from app.features.retrieval.schemas import RetrievalMessage


def is_authorized_for_source(data_source: str, tools: list[str]) -> bool:
    data_source = data_source.strip()
    for tool in tools:
        if data_source == tool or data_source.startswith(tool):
            return True
    return False


def resolve_conversation_id(payload) -> str:
    if isinstance(payload.chat_id, str) and payload.chat_id.strip():
        return payload.chat_id.strip()
    return f"conv-{uuid4_str()}"


def extract_last_user_message(messages: list[RetrievalMessage]) -> str:
    for message in reversed(messages):
        if message.role == "user" and message.content.strip():
            return message.content.strip()
    return ""


def format_sources(results, max_chars: int) -> str:
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


def resolve_result_titles(results) -> list[str]:
    titles: list[str] = []
    for result in results:
        title = result.title or result.url
        if title:
            titles.append(title)
    return titles


def resolve_search_method(provider_id: str, query_embedding: list[float] | None) -> str:
    if query_embedding:
        return "hybrid" if provider_id == "ai-search" else "vector"
    return "keyword"


def resolve_index_name(app_config, provider_id: str, data_source: str) -> str:
    if provider_id == "local-files":
        base = app_config.retrieval_local_path
        if data_source:
            return str((base + "/" + data_source).rstrip("/"))
        return str(base)
    return data_source


def resolve_embedding_model(provider_id: str, query_embedding: list[float] | None) -> str | None:
    if not query_embedding:
        return None
    return "unknown"


def resolve_zero_reason(
    *,
    provider_id: str,
    data_source: str,
    query: str,
    query_embedding: list[float] | None,
) -> str:
    if not query.strip():
        return "QUERY_TOO_GENERIC"
    return "NO_DOCUMENT_IN_INDEX"


def build_answer_payload(
    *,
    system_prompt: str,
    messages: list[RetrievalMessage],
    query: str,
    sources: str,
) -> list[dict[str, str]]:
    user_prompt = PromptTemplate.from_template("{query}\n\nSources:\n{sources}")
    user_payload = query if not sources else user_prompt.format(query=query, sources=sources)
    history = [
        {"role": message.role, "content": message.content}
        for message in messages
        if message.content
    ]
    return [
        {"role": "system", "content": system_prompt},
        *history,
        {"role": "user", "content": user_payload},
    ]


def extract_delta(chunk: BaseMessage | AIMessageChunk) -> str:
    content = getattr(chunk, "content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        text_parts = [
            part.get("text", "")
            for part in content
            if isinstance(part, dict) and part.get("type") == "text"
        ]
        return "".join(text_parts)
    return ""


def truncate_text(text: str, limit: int = 160) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def preview_payload(payload: Any, limit: int = 160) -> str:
    serialized = json.dumps(payload, ensure_ascii=True, default=str)
    return truncate_text(serialized, limit)


def uuid4_str() -> str:
    from uuid import uuid4

    return str(uuid4())
