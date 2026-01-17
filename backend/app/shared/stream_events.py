from fastapi_ai_sdk.models import (
    ErrorEvent,
    StartEvent,
    TextDeltaEvent,
    TextEndEvent,
    TextStartEvent,
)


def build_start_event(message_id: str) -> StartEvent:
    return StartEvent(messageId=message_id)


def build_text_start_event(text_id: str) -> TextStartEvent:
    return TextStartEvent(id=text_id)


def build_text_delta_event(text_id: str, delta: str) -> TextDeltaEvent:
    return TextDeltaEvent(id=text_id, delta=delta)


def build_text_end_event(text_id: str) -> TextEndEvent:
    return TextEndEvent(id=text_id)


def build_error_event(message: str) -> ErrorEvent:
    return ErrorEvent(errorText=message)
