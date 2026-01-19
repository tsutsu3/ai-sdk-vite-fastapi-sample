import uuid
from dataclasses import dataclass
from logging import getLogger

from app.features.authz.models import (
    MembershipRecord,
    MembershipStatus,
    TenantRecord,
    UserIdentityRecord,
    UserInfo,
    UserRecord,
)
from app.features.authz.ports import AuthzRepository
from app.shared.time import now_datetime

logger = getLogger(__name__)


class AuthzError(RuntimeError):
    """Authorization flow error."""


@dataclass(frozen=True)
class AuthzResolution:
    user_record: UserRecord
    tenant_record: TenantRecord
    user_identity: UserIdentityRecord
    membership: MembershipRecord


class AuthzService:
    def __init__(self, repo: AuthzRepository) -> None:
        self._repo = repo

    async def resolve_access(self, user: UserInfo) -> AuthzResolution:
        logger.debug(
            "Resolve authz started user_id=%s provider=%s",
            user.id,
            user.provider,
        )
        user_identity = await self._repo.get_user_identity(user.id)
        if user_identity:
            user_record = await self._repo.get_user(user_identity.user_id)
            if not user_record:
                logger.warning("Authz records missing user_id=%s", user.id)
                raise AuthzError("User is not authorized for any tenant")
            active_tenant_id = user_record.active_tenant_id
            if not active_tenant_id:
                memberships = await self._repo.list_memberships_by_user(user_record.id)
                active = next(
                    (
                        record
                        for record in memberships
                        if record.status == MembershipStatus.ACTIVE
                    ),
                    None,
                )
                if not active:
                    logger.warning("Authz tenant missing user_id=%s", user.id)
                    raise AuthzError("User is not authorized for any tenant")
                active_tenant_id = active.tenant_id
                user_record = user_record.model_copy(
                    update={
                        "active_tenant_id": active_tenant_id,
                        "updated_at": now_datetime(),
                    }
                )
                await self._repo.save_user(user_record)
            tenant_record = await self._repo.get_tenant(active_tenant_id)
            if not tenant_record:
                logger.warning("Authz tenant missing user_id=%s", user.id)
                raise AuthzError("User is not authorized for any tenant")
            membership = await self._repo.get_membership_for_user(
                active_tenant_id, user_record.id
            )
            if not membership or membership.status != MembershipStatus.ACTIVE:
                logger.warning(
                    "Authz membership missing user_id=%s tenant_id=%s",
                    user_record.id,
                    active_tenant_id,
                )
                raise AuthzError("User is not authorized for any tenant")
            logger.debug(
                "Authz resolved from cache user_id=%s tenant_id=%s",
                user_record.id,
                active_tenant_id,
            )
            return AuthzResolution(
                user_record=user_record,
                tenant_record=tenant_record,
                user_identity=user_identity,
                membership=membership,
            )

        if not user.email:
            logger.warning("Authz email missing user_id=%s", user.id)
            raise AuthzError("User email is required for membership")

        membership_matches = await self._repo.list_memberships_by_email(
            user.email, MembershipStatus.PENDING
        )
        if len(membership_matches) != 1:
            logger.warning(
                "Authz membership unavailable user_id=%s matches=%d",
                user.id,
                len(membership_matches),
            )
            raise AuthzError("User membership is not available")
        membership = membership_matches[0]

        logger.info(
            "Authz membership activation started user_id=%s tenant_id=%s",
            user.id,
            membership.tenant_id,
        )
        user_record = UserRecord(
            id=str(uuid.uuid4()),
            active_tenant_id=membership.tenant_id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            created_at=now_datetime(),
            updated_at=now_datetime(),
        )
        await self._repo.save_user(user_record)

        user_identity = UserIdentityRecord(
            id=user.id,
            provider=user.provider,
            user_id=user_record.id,
            created_at=now_datetime(),
            updated_at=now_datetime(),
        )
        await self._repo.save_user_identity(user_identity)

        membership = membership.model_copy(
            update={
                "status": MembershipStatus.ACTIVE,
                "user_id": user_record.id,
                "updated_at": now_datetime(),
            }
        )
        await self._repo.save_membership(membership)

        tenant_record = await self._repo.get_tenant(user_record.active_tenant_id)
        if not tenant_record:
            logger.warning(
                "Authz tenant missing user_id=%s tenant_id=%s",
                user_record.id,
                user_record.active_tenant_id,
            )
            raise AuthzError("Tenant is not authorized")

        logger.info(
            "Authz membership activation complete user_id=%s tenant_id=%s",
            user_record.id,
            user_record.active_tenant_id,
        )
        return AuthzResolution(
            user_record=user_record,
            tenant_record=tenant_record,
            user_identity=user_identity,
            membership=membership,
        )
