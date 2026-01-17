from contextvars import ContextVar, Token
from uuid import uuid4

from fastapi import Request

_REQUEST_ID_CTX: ContextVar[str | None] = ContextVar("request_id", default=None)


def generate_request_id() -> str:
    return uuid4().hex


def get_current_request_id() -> str | None:
    return _REQUEST_ID_CTX.get()


def set_request_id(request: Request, request_id: str) -> Token[str | None]:
    request.state.request_id = request_id
    return _REQUEST_ID_CTX.set(request_id)


def reset_request_id(token: Token[str | None]) -> None:
    _REQUEST_ID_CTX.reset(token)
