from collections.abc import AsyncGenerator
from contextvars import ContextVar

from fastapi import HTTPException, Request

from app.features.authz.identity import parse_user_from_headers
from app.features.authz.models import (
    TenantRecord,
    UserIdentityRecord,
    UserInfo,
    UserRecord,
)
from app.features.authz.service import AuthzError, AuthzService

_tenant_id_ctx: ContextVar[str | None] = ContextVar("tenant_id", default=None)
_user_id_ctx: ContextVar[str | None] = ContextVar("user_id", default=None)
_user_info_ctx: ContextVar[UserInfo | None] = ContextVar("user_info", default=None)
_user_record_ctx: ContextVar[UserRecord | None] = ContextVar("user_record", default=None)
_tenant_record_ctx: ContextVar[TenantRecord | None] = ContextVar("tenant_record", default=None)
_user_identity_ctx: ContextVar[UserIdentityRecord | None] = ContextVar(
    "user_identity", default=None
)


def get_current_tenant_id() -> str:
    """Return the current tenant id from context.

    Returns:
        str: Tenant identifier.
    """
    tenant_id = _tenant_id_ctx.get()
    if not tenant_id:
        raise RuntimeError("tenant_id is not set in request context")
    return tenant_id


def get_current_user_id() -> str:
    """Return the current user id from context.

    Returns:
        str: User identifier.
    """
    user_id = _user_id_ctx.get()
    if not user_id:
        raise RuntimeError("user_id is not set in request context")
    return user_id


def get_current_user_record() -> UserRecord | None:
    """Return the current user record from context.

    Returns:
        UserRecord | None: User record if present.
    """
    return _user_record_ctx.get()


def get_current_tenant_record() -> TenantRecord | None:
    """Return the current tenant record from context.

    Returns:
        TenantRecord | None: Tenant record if present.
    """
    return _tenant_record_ctx.get()


def get_current_user_identity() -> UserIdentityRecord | None:
    """Return the current user identity record from context.

    Returns:
        UserIdentityRecord | None: User identity record if present.
    """
    return _user_identity_ctx.get()


def get_current_user_info() -> UserInfo | None:
    """Return the current user info from context.

    Returns:
        UserInfo | None: User info if present.
    """
    return _user_info_ctx.get()


def get_tenant_id(request: Request) -> str:
    """Extract tenant id from request state.

    Args:
        request: Incoming request.

    Returns:
        str: Tenant identifier.
    """
    tenant_id: str | None = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise RuntimeError("tenant_id is not set in request.state")
    return tenant_id


def get_user_id(request: Request) -> str:
    """Extract user id from request state.

    Args:
        request: Incoming request.

    Returns:
        str: User identifier.
    """
    user_id: str | None = getattr(request.state, "user_id", None)
    if not user_id:
        raise RuntimeError("user_id is not set in request.state")
    return user_id


async def require_request_context(request: Request) -> AsyncGenerator[None, None]:
    """Populate request-scoped context values required for access control.

    This dependency resolves the authenticated user and raw authz records,
    sets request-scoped context variables (tenant, user, records),
    and ensures the request is authorized for at least one tenant.

    Args:
        request: Incoming request.

    Yields:
        None: Control back to request handling.
    """
    user = parse_user_from_headers(request)
    service: AuthzService = request.app.state.authz_service

    try:
        resolution = await service.resolve_access(user)
    except AuthzError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    user_record = resolution.user_record
    tenant_record = resolution.tenant_record
    user_identity = resolution.user_identity

    if not user_record.id:
        raise HTTPException(status_code=403, detail="User record id is missing")

    token_tenant = _tenant_id_ctx.set(user_record.tenant_id)
    token_user = _user_id_ctx.set(user_record.id)
    token_user_info = _user_info_ctx.set(user)
    token_user_record = _user_record_ctx.set(user_record)
    token_tenant_record = _tenant_record_ctx.set(tenant_record)
    token_user_identity = _user_identity_ctx.set(user_identity)

    request.state.tenant_id = user_record.tenant_id
    request.state.user_id = user_record.id
    request.state.user_record = user_record
    request.state.tenant_record = tenant_record
    request.state.user_identity = user_identity

    try:
        yield
    finally:
        _tenant_id_ctx.reset(token_tenant)
        _user_id_ctx.reset(token_user)
        _user_info_ctx.reset(token_user_info)
        _user_record_ctx.reset(token_user_record)
        _tenant_record_ctx.reset(token_tenant_record)
        _user_identity_ctx.reset(token_user_identity)
