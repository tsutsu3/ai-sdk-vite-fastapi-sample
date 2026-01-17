import uuid
from dataclasses import dataclass
from logging import getLogger

from app.features.authz.models import (
    ProvisioningStatus,
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
            tenant_record = await self._repo.get_tenant(user_identity.tenant_id)
            if not user_record or not tenant_record:
                logger.warning("Authz records missing user_id=%s", user.id)
                raise AuthzError("User is not authorized for any tenant")
            logger.debug(
                "Authz resolved from cache user_id=%s tenant_id=%s",
                user_record.id,
                user_record.tenant_id,
            )
            return AuthzResolution(
                user_record=user_record,
                tenant_record=tenant_record,
                user_identity=user_identity,
            )

        if not user.email:
            logger.warning("Authz email missing user_id=%s", user.id)
            raise AuthzError("User email is required for provisioning")

        provisioning_matches = await self._repo.list_provisioning_by_email(
            user.email, ProvisioningStatus.PENDING
        )
        if len(provisioning_matches) != 1:
            logger.warning(
                "Authz provisioning unavailable user_id=%s matches=%d",
                user.id,
                len(provisioning_matches),
            )
            raise AuthzError("User provisioning is not available")
        provisioning = provisioning_matches[0]

        logger.info(
            "Authz provisioning started user_id=%s tenant_id=%s",
            user.id,
            provisioning.tenant_id,
        )
        user_record = UserRecord(
            id=str(uuid.uuid4()),
            tenant_id=provisioning.tenant_id,
            email=user.email,
            first_name=provisioning.first_name,
            last_name=provisioning.last_name,
            tool_overrides=provisioning.tool_overrides,
            created_at=now_datetime(),
            updated_at=now_datetime(),
        )
        await self._repo.save_user(user_record)

        user_identity = UserIdentityRecord(
            id=user.id,
            provider=user.provider,
            user_id=user_record.id,
            tenant_id=user_record.tenant_id,
            created_at=now_datetime(),
            updated_at=now_datetime(),
        )
        await self._repo.save_user_identity(user_identity)

        provisioning = provisioning.model_copy(
            update={
                "status": ProvisioningStatus.ACTIVE,
                "updated_at": now_datetime(),
            }
        )
        await self._repo.save_provisioning(provisioning)

        tenant_record = await self._repo.get_tenant(user_record.tenant_id)
        if not tenant_record:
            logger.warning(
                "Authz tenant missing user_id=%s tenant_id=%s",
                user_record.id,
                user_record.tenant_id,
            )
            raise AuthzError("Tenant is not authorized")

        logger.info(
            "Authz provisioning complete user_id=%s tenant_id=%s",
            user_record.id,
            user_record.tenant_id,
        )
        return AuthzResolution(
            user_record=user_record,
            tenant_record=tenant_record,
            user_identity=user_identity,
        )
