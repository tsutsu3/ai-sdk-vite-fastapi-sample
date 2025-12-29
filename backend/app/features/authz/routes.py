from fastapi import APIRouter, Depends

from app.core.dependencies import get_authz_repository
from app.features.authz.models import UserInfo
from app.features.authz.ports import AuthzRepository
from app.features.authz.request_context import (
    get_current_tenant_record,
    get_current_user_info,
    get_current_user_record,
    require_request_context,
)
from app.features.authz.schemas import AuthorizationResponse
from app.features.authz.tool_merge import merge_tools
from app.features.authz.tools import TOOL_GROUPS

router = APIRouter(dependencies=[Depends(require_request_context)])


@router.get(
    "/authz",
    response_model=AuthorizationResponse,
    tags=["Authz"],
    summary="Get user authorization",
    description=("Returns the authenticated user's profile and tool permissions."),
    response_description="Authorization details for the current user.",
)
async def get_authorization(
    repo: AuthzRepository = Depends(get_authz_repository),
) -> AuthorizationResponse:
    """Return access control for the current user.

    Resolves the authenticated user and returns their tool permissions for UI
    rendering.
    """
    user = get_current_user_info()
    if user is None:
        raise RuntimeError("User info is not set in request context")

    user_record = get_current_user_record()
    tenant_record = get_current_tenant_record()
    if user_record is None:
        user_identity = await repo.get_user_identity(user.id)
        if user_identity is None:
            raise RuntimeError("User identity is not set in request context")
        user_record = await repo.get_user(user_identity.user_id)
    if user_record is None or not user_record.tenant_id:
        raise RuntimeError("User record is not set in request context")
    if tenant_record is None:
        tenant_record = await repo.get_tenant(user_record.tenant_id)
    if tenant_record is None:
        raise RuntimeError("Tenant record is not set in request context")

    tools = merge_tools(tenant_record.default_tools, user_record.tool_overrides)
    tool_groups = [group for group in TOOL_GROUPS if group.id in tools]
    return AuthorizationResponse(
        user=UserInfo(
            id=user.id,
            email=user_record.email,
            provider=user.provider,
            first_name=user_record.first_name,
            last_name=user_record.last_name,
        ),
        tools=tools,
        toolGroups=tool_groups,
    )
