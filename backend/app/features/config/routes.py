import logging

from fastapi import APIRouter, Depends, HTTPException

from app.core.dependencies import get_authz_repository
from app.features.authz.models import MembershipStatus, UserInfo
from app.features.authz.ports import AuthzRepository
from app.features.authz.request_context import (
    get_current_user_identity,
    get_current_user_info,
    get_current_user_record,
)
from app.features.config.schemas import ConfigResponse, ConfigUpdateRequest, TenantSummary
from app.shared.time import now_datetime

logger = logging.getLogger(__name__)
router = APIRouter()


def _normalize_tenant_ids(tenant_ids: list[str]) -> list[str]:
    normalized = [tenant_id.strip() for tenant_id in tenant_ids if tenant_id.strip()]
    return list(dict.fromkeys(normalized))


def _active_tenant_ids(memberships) -> list[str]:
    return [record.tenant_id for record in memberships if record.status == MembershipStatus.ACTIVE]


async def _load_user_record(
    user: UserInfo,
    repo: AuthzRepository,
):
    user_record = get_current_user_record()
    if user_record is not None:
        return user_record
    user_identity = get_current_user_identity()
    if user_identity is None:
        user_identity = await repo.get_user_identity(user.id)
    if user_identity is None:
        raise RuntimeError("User identity is not set in request context")
    user_record = await repo.get_user(user_identity.user_id)
    if user_record is None:
        raise RuntimeError("User record is not set in request context")
    return user_record


async def _load_tenant_summaries(
    repo: AuthzRepository, tenant_ids: list[str]
) -> list[TenantSummary]:
    summaries: list[TenantSummary] = []
    for tenant_id in tenant_ids:
        tenant_record = await repo.get_tenant(tenant_id)
        if tenant_record is None:
            logger.warning("config.tenant.missing tenant_id=%s", tenant_id)
            continue
        summaries.append(
            TenantSummary(
                id=tenant_record.id,
                key=tenant_record.key,
                name=tenant_record.name,
            )
        )
    return summaries


@router.get(
    "/config",
    response_model=ConfigResponse,
    tags=["Config"],
    summary="Get user configuration",
    description="Returns the authenticated user's tenant configuration.",
    response_description="Configuration for the current user.",
)
async def get_config(
    repo: AuthzRepository = Depends(get_authz_repository),
) -> ConfigResponse:
    user = get_current_user_info()
    if user is None:
        raise RuntimeError("User info is not set in request context")

    user_record = await _load_user_record(user, repo)
    memberships = await repo.list_memberships_by_user(user_record.id)
    tenant_ids = _normalize_tenant_ids(_active_tenant_ids(memberships))
    active_tenant_id = user_record.active_tenant_id
    if not active_tenant_id or active_tenant_id not in tenant_ids:
        raise HTTPException(status_code=403, detail="Active tenant is not authorized")

    tenant_summaries = await _load_tenant_summaries(repo, tenant_ids)
    if not any(summary.id == active_tenant_id for summary in tenant_summaries):
        raise HTTPException(status_code=403, detail="Active tenant is not authorized")

    return ConfigResponse(
        user=UserInfo(
            id=user.id,
            email=user_record.email,
            provider=user.provider,
            first_name=user_record.first_name,
            last_name=user_record.last_name,
        ),
        tenant_ids=tenant_ids,
        active_tenant_id=active_tenant_id,
        tenants=tenant_summaries,
    )


@router.patch(
    "/config",
    response_model=ConfigResponse,
    tags=["Config"],
    summary="Update user configuration",
    description="Updates the active tenant for the current user.",
    response_description="Updated configuration for the current user.",
)
async def update_config(
    payload: ConfigUpdateRequest,
    repo: AuthzRepository = Depends(get_authz_repository),
) -> ConfigResponse:
    user = get_current_user_info()
    if user is None:
        raise RuntimeError("User info is not set in request context")

    user_record = await _load_user_record(user, repo)
    memberships = await repo.list_memberships_by_user(user_record.id)
    tenant_ids = _normalize_tenant_ids(_active_tenant_ids(memberships))
    if payload.active_tenant_id not in tenant_ids:
        raise HTTPException(status_code=403, detail="Tenant is not authorized")

    if payload.active_tenant_id != user_record.active_tenant_id:
        user_record = user_record.model_copy(
            update={
                "active_tenant_id": payload.active_tenant_id,
                "updated_at": now_datetime(),
            }
        )
        await repo.save_user(user_record)
        logger.info(
            "config.active_tenant.updated user_id=%s tenant_id=%s",
            user_record.id,
            user_record.active_tenant_id,
        )

    tenant_summaries = await _load_tenant_summaries(repo, tenant_ids)
    if not any(
        summary.id == user_record.active_tenant_id for summary in tenant_summaries
    ):
        raise HTTPException(status_code=403, detail="Active tenant is not authorized")

    return ConfigResponse(
        user=UserInfo(
            id=user.id,
            email=user_record.email,
            provider=user.provider,
            first_name=user_record.first_name,
            last_name=user_record.last_name,
        ),
        tenant_ids=tenant_ids,
        active_tenant_id=user_record.active_tenant_id,
        tenants=tenant_summaries,
    )
