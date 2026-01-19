from contextvars import ContextVar, Token
from dataclasses import dataclass
from logging import getLogger

from fastapi import HTTPException, Request

from app.features.authz.identity import parse_user_from_headers
from app.features.authz.models import (
    MembershipRecord,
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
_membership_ctx: ContextVar[MembershipRecord | None] = ContextVar(
    "membership", default=None
)

logger = getLogger(__name__)


@dataclass(frozen=True)
class AuthzRequestContext:
    """Resolved authorization context for the current request."""

    user: UserInfo
    user_record: UserRecord
    tenant_record: TenantRecord
    user_identity: UserIdentityRecord
    membership: MembershipRecord


@dataclass(frozen=True)
class RequestContextTokens:
    """Context variable tokens for safe reset after request handling."""

    tenant_id: Token[str | None]
    user_id: Token[str | None]
    user_info: Token[UserInfo | None]
    user_record: Token[UserRecord | None]
    tenant_record: Token[TenantRecord | None]
    user_identity: Token[UserIdentityRecord | None]
    membership: Token[MembershipRecord | None]


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


def get_current_membership() -> MembershipRecord | None:
    """Return the current membership record from context."""
    return _membership_ctx.get()


def get_current_user_info() -> UserInfo | None:
    """Return the current user info from context.

    Returns:
        UserInfo | None: User info if present.
    """
    return _user_info_ctx.get()


async def resolve_request_context(request: Request) -> AuthzRequestContext:
    """Resolve the authenticated user and authorization records.

    Args:
        request: Incoming request.

    Returns:
        AuthzRequestContext: Resolved authorization context.
    """
    user = parse_user_from_headers(request)
    logger.debug("authz.resolve.start provider=%s", user.provider)
    service: AuthzService = request.app.state.authz_service

    try:
        resolution = await service.resolve_access(user)
    except AuthzError as exc:
        logger.info("authz.resolve.denied reason=%s", str(exc))
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    user_record = resolution.user_record
    if not user_record.id:
        raise HTTPException(status_code=403, detail="User record id is missing")

    return AuthzRequestContext(
        user=user,
        user_record=user_record,
        tenant_record=resolution.tenant_record,
        user_identity=resolution.user_identity,
        membership=resolution.membership,
    )


def set_request_context(
    request: Request,
    context: AuthzRequestContext,
) -> RequestContextTokens:
    """Populate context vars and request state from an authz context.

    Args:
        request: Incoming request.
        context: Resolved authorization context.

    Returns:
        RequestContextTokens: Tokens for resetting context variables.
    """
    token_tenant = _tenant_id_ctx.set(context.user_record.active_tenant_id)
    token_user = _user_id_ctx.set(context.user_record.id)
    token_user_info = _user_info_ctx.set(context.user)
    token_user_record = _user_record_ctx.set(context.user_record)
    token_tenant_record = _tenant_record_ctx.set(context.tenant_record)
    token_user_identity = _user_identity_ctx.set(context.user_identity)
    token_membership = _membership_ctx.set(context.membership)

    request.state.tenant_id = context.user_record.active_tenant_id
    request.state.user_id = context.user_record.id
    request.state.user_record = context.user_record
    request.state.tenant_record = context.tenant_record
    request.state.user_identity = context.user_identity
    request.state.membership = context.membership

    logger.info(
        "authz.resolve.success tenant_id=%s user_id=%s",
        context.user_record.active_tenant_id,
        context.user_record.id,
    )

    return RequestContextTokens(
        tenant_id=token_tenant,
        user_id=token_user,
        user_info=token_user_info,
        user_record=token_user_record,
        tenant_record=token_tenant_record,
        user_identity=token_user_identity,
        membership=token_membership,
    )


def reset_request_context(tokens: RequestContextTokens) -> None:
    """Reset context variables after request handling."""
    _tenant_id_ctx.reset(tokens.tenant_id)
    _user_id_ctx.reset(tokens.user_id)
    _user_info_ctx.reset(tokens.user_info)
    _user_record_ctx.reset(tokens.user_record)
    _tenant_record_ctx.reset(tokens.tenant_record)
    _user_identity_ctx.reset(tokens.user_identity)
    _membership_ctx.reset(tokens.membership)
