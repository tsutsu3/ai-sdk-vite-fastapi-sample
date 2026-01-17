from collections.abc import Iterable
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from app.features.messages.models import MessageRecord


def to_langchain_messages_from_records(messages: list[MessageRecord]) -> list[BaseMessage]:
    """Convert stored chat messages into LangChain BaseMessage objects."""
    converted: list[BaseMessage] = []
    for message in messages:
        text_parts = [part.text or "" for part in message.parts if part.type == "text"]
        content = " ".join(part.strip() for part in text_parts if part).strip()
        if content:
            converted.append(_role_to_message(message.role, content))
    return converted


def to_langchain_messages_from_roles(messages: Iterable[Any]) -> list[BaseMessage]:
    """Convert role/content items into LangChain BaseMessage objects."""
    converted: list[BaseMessage] = []
    for message in messages:
        if isinstance(message, dict):
            role = str(message.get("role") or "")
            content = str(message.get("content") or "")
        else:
            role = str(getattr(message, "role", ""))
            content = str(getattr(message, "content", ""))
        if content:
            converted.append(_role_to_message(role, content))
    return converted


def _role_to_message(role: str, content: str) -> BaseMessage:
    normalized = role.lower().strip()
    if normalized == "system":
        return SystemMessage(content=content)
    if normalized == "assistant":
        return AIMessage(content=content)
    return HumanMessage(content=content)
