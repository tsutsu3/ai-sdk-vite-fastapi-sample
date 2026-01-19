from fastapi import APIRouter, Depends

from app.core.dependencies import get_authz_repository, get_tool_catalog_repository
from app.features.authz.models import MembershipStatus, UserInfo
from app.features.authz.ports import AuthzRepository
from app.features.authz.request_context import (
    get_current_membership,
    get_current_tenant_record,
    get_current_user_info,
    get_current_user_record,
)
from app.features.authz.schemas import AuthorizationResponse
from app.features.authz.tool_merge import merge_tools
from app.features.authz.tools import build_tool_groups
from app.features.tool_catalog.ports import ToolCatalogRepository

router = APIRouter()


@router.get(
    "/authz",
    response_model=AuthorizationResponse,
    tags=["Authz"],
    summary="Get user authorization",
    description=("Returns the authenticated user's profile and tool permissions."),
    response_description="Authorization details for the current user.",
    responses={
        422: {
            "description": "Validation Error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["query", "include"],
                                "msg": "Input should be a valid boolean",
                                "type": "bool_parsing",
                            }
                        ]
                    }
                }
            },
        }
    },
)
async def get_authorization(
    repo: AuthzRepository = Depends(get_authz_repository),
    tool_catalog: ToolCatalogRepository = Depends(get_tool_catalog_repository),
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
    membership = get_current_membership()
    if user_record is None:
        user_identity = await repo.get_user_identity(user.id)
        if user_identity is None:
            raise RuntimeError("User identity is not set in request context")
        user_record = await repo.get_user(user_identity.user_id)
    if user_record is None or not user_record.active_tenant_id:
        raise RuntimeError("User record is not set in request context")
    if membership is None:
        membership = await repo.get_membership_for_user(
            user_record.active_tenant_id, user_record.id
        )
    if membership is None or membership.status != MembershipStatus.ACTIVE:
        raise RuntimeError("Membership is not set in request context")
    if tenant_record is None:
        tenant_record = await repo.get_tenant(user_record.active_tenant_id)
    if tenant_record is None:
        raise RuntimeError("Tenant record is not set in request context")

    tools = await tool_catalog.list_tools(user_record.active_tenant_id)
    available_tool_ids = {tool.id for tool in tools if tool.enabled}
    allowed_tool_ids = merge_tools(
        tenant_record.default_tool_ids,
        membership.tool_overrides,
        available_tool_ids=available_tool_ids,
    )
    tool_groups = build_tool_groups(tools, allowed_tool_ids)
    return AuthorizationResponse(
        user=UserInfo(
            id=user.id,
            email=user_record.email,
            provider=user.provider,
            first_name=user_record.first_name,
            last_name=user_record.last_name,
        ),
        tools=allowed_tool_ids,
        toolGroups=tool_groups,
    )
