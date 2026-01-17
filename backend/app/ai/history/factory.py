from collections.abc import Callable

from langchain_core.chat_history import (
    BaseChatMessageHistory,
    InMemoryChatMessageHistory,
)

from app.ai.history.message_history import (
    HistoryKey,
    RepositoryChatMessageHistory,
    parse_history_key,
)
from app.ai.models import MemoryPolicy
from app.features.messages.ports import MessageRepository


def build_history_factory(
    repo: MessageRepository | None,
    policy: MemoryPolicy,
    *,
    write_enabled: bool = True,
) -> Callable[[str], BaseChatMessageHistory]:
    def factory(session_id: str) -> BaseChatMessageHistory:
        if repo is None:
            return InMemoryChatMessageHistory()
        key = parse_history_key(session_id)
        window_size = policy.window_size if policy.type == "window" else None
        return RepositoryChatMessageHistory(
            repo,
            key,
            window_size=window_size,
            write_enabled=write_enabled,
        )

    return factory


def build_session_id(key: HistoryKey) -> str:
    return f"{key.tenant_id}::{key.user_id}::{key.conversation_id}"
