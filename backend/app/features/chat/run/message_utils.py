import uuid

from langchain_core.messages import BaseMessage

from app.features.chat.run.models import RunRequest
from app.features.messages.models import MessageRecord
from app.shared.langchain_utils import to_langchain_messages_from_records


def extract_messages(payload: RunRequest) -> list[MessageRecord]:
    """Extract chat messages from a request payload."""
    return list(payload.messages)


def select_latest_user_message(messages: list[MessageRecord]) -> list[MessageRecord]:
    """Return only the most recent user message for the payload."""
    for message in reversed(messages):
        if message.role == "user":
            return [message]
    return messages[-1:] if messages else []


def extract_conversation_id(payload: RunRequest) -> str:
    """Resolve a conversation id from the payload or create one."""
    if isinstance(payload.chat_id, str) and payload.chat_id:
        return payload.chat_id
    return f"conv-{uuid.uuid4()}"


def extract_model_id(payload: RunRequest) -> str | None:
    """Extract the model id from a payload."""
    model = payload.model
    if isinstance(model, str) and model:
        return model
    for message in reversed(payload.messages):
        if message.model_id:
            return message.model_id
    return None


def extract_file_ids(payload: RunRequest) -> list[str]:
    """Extract file ids from a payload."""
    if not payload.file_ids:
        return []
    return [str(file_id) for file_id in payload.file_ids]


def to_langchain_messages(messages: list[MessageRecord]) -> list[BaseMessage]:
    """Convert stored chat messages into LangChain BaseMessage objects."""
    return to_langchain_messages_from_records(messages)
