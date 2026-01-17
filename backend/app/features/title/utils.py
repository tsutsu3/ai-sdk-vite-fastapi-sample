from app.features.messages.models import MessageRecord
from app.shared.constants import DEFAULT_CHAT_TITLE


def extract_message_text(message: MessageRecord) -> str:
    """Extract text content from a message record."""
    text_parts = [part.text or "" for part in message.parts if part.type == "text"]
    text = " ".join(part.strip() for part in text_parts if part)
    return text.strip() if text.strip() else ""


def generate_fallback_title(messages: list[MessageRecord]) -> str:
    """Generate a fallback title from message content."""
    for message in messages:
        if message.role == "user":
            text = extract_message_text(message)
            if text:
                words = text.split()
                title = " ".join(words[:6])
                return title[:20].rstrip() or DEFAULT_CHAT_TITLE
    return DEFAULT_CHAT_TITLE
