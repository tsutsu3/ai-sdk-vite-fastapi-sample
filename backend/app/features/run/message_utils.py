import uuid

from app.features.messages.models import MessageRecord
from app.features.run.models import OpenAIMessage, RunRequest


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


def to_openai_messages(messages: list[MessageRecord]) -> list[OpenAIMessage]:
    """Convert chat messages to OpenAI-style messages."""
    converted: list[OpenAIMessage] = []
    for message in messages:
        text_parts = [part.text or "" for part in message.parts if part.type == "text"]
        content = " ".join(part.strip() for part in text_parts if part).strip()
        if content:
            converted.append(OpenAIMessage(role=message.role, content=content))
    return converted
