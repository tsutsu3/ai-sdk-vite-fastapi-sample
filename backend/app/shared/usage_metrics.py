import json
from typing import Any


def compute_bytes_in(payload: list[dict[str, Any]] | None) -> int | None:
    if not payload:
        return None
    return len(json.dumps(payload).encode("utf-8"))


def compute_bytes_out(response_text: str | None) -> int | None:
    if not response_text:
        return None
    return len(response_text.encode("utf-8"))
