from typing import Any


def extract_message_text(message: dict[str, Any]) -> str:
    parts = message.get("parts")
    if isinstance(parts, list):
        text_parts = [
            part.get("text", "")
            for part in parts
            if isinstance(part, dict) and part.get("type") == "text"
        ]
        text = " ".join(part.strip() for part in text_parts if part)
        if text.strip():
            return text.strip()
    content = message.get("content")
    if isinstance(content, str) and content.strip():
        return content.strip()
    return ""


from app.shared.constants import DEFAULT_CHAT_TITLE


def generate_fallback_title(messages: list[dict]) -> str:
    for message in messages:
        if message.get("role") == "user":
            text = extract_message_text(message)
            if text:
                words = text.split()
                title = " ".join(words[:6])
                return title[:60].rstrip() or DEFAULT_CHAT_TITLE
    return DEFAULT_CHAT_TITLE
