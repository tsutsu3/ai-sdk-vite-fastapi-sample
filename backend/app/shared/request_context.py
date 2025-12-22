from collections.abc import AsyncGenerator
from contextvars import ContextVar
from typing import cast

from fastapi import HTTPException, Request

from app.features.authz.identity import parse_user_from_headers
from app.features.authz.models import AuthzRecord, UserInfo
from app.features.authz.repository.authz_repository import AuthzRepository

_tenant_id_ctx: ContextVar[str | None] = ContextVar("tenant_id", default=None)
_user_id_ctx: ContextVar[str | None] = ContextVar("user_id", default=None)
_authz_ctx: ContextVar[AuthzRecord | None] = ContextVar("authz_record", default=None)
_user_info_ctx: ContextVar[UserInfo | None] = ContextVar("user_info", default=None)


def get_current_tenant_id() -> str:
    tenant_id = _tenant_id_ctx.get()
    if not tenant_id:
        raise RuntimeError("tenant_id is not set in request context")
    return tenant_id


def get_current_user_id() -> str:
    user_id = _user_id_ctx.get()
    if not user_id:
        raise RuntimeError("user_id is not set in request context")
    return user_id


def get_current_authz_record() -> AuthzRecord | None:
    return _authz_ctx.get()


def get_current_user_info() -> UserInfo | None:
    return _user_info_ctx.get()


def get_tenant_id(request: Request) -> str:
    tenant_id: str | None = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise RuntimeError("tenant_id is not set in request.state")
    return tenant_id


def get_user_id(request: Request) -> str:
    user_id: str | None = getattr(request.state, "user_id", None)
    if not user_id:
        raise RuntimeError("user_id is not set in request.state")
    return user_id


async def require_request_context(request: Request) -> AsyncGenerator[None, None]:
    repo = cast(AuthzRepository, request.app.state.authz_repository)
    user = parse_user_from_headers(request)
    record = await repo.get_authz(user.user_id)
    if not record or not record.tenant_id:
        raise HTTPException(status_code=403, detail="User is not authorized for any tenant")

    token_tenant = _tenant_id_ctx.set(record.tenant_id)
    token_user = _user_id_ctx.set(user.user_id)
    token_authz = _authz_ctx.set(record)
    token_user_info = _user_info_ctx.set(user)
    request.state.tenant_id = record.tenant_id
    request.state.user_id = user.user_id
    request.state.authz_record = record
    try:
        yield
    finally:
        _tenant_id_ctx.reset(token_tenant)
        _user_id_ctx.reset(token_user)
        _authz_ctx.reset(token_authz)
        _user_info_ctx.reset(token_user_info)
