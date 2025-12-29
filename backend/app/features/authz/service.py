import uuid
from dataclasses import dataclass

from app.features.authz.models import (
    ProvisioningStatus,
    TenantRecord,
    UserIdentityRecord,
    UserInfo,
    UserRecord,
)
from app.features.authz.ports import AuthzRepository
from app.shared.time import now_datetime


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
        user_identity = await self._repo.get_user_identity(user.id)
        if user_identity:
            user_record = await self._repo.get_user(user_identity.user_id)
            tenant_record = await self._repo.get_tenant(user_identity.tenant_id)
            if not user_record or not tenant_record:
                raise AuthzError("User is not authorized for any tenant")
            return AuthzResolution(
                user_record=user_record,
                tenant_record=tenant_record,
                user_identity=user_identity,
            )

        if not user.email:
            raise AuthzError("User email is required for provisioning")

        provisioning_matches = await self._repo.list_provisioning_by_email(
            user.email, ProvisioningStatus.PENDING
        )
        if len(provisioning_matches) != 1:
            raise AuthzError("User provisioning is not available")
        provisioning = provisioning_matches[0]

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
            raise AuthzError("Tenant is not authorized")

        return AuthzResolution(
            user_record=user_record,
            tenant_record=tenant_record,
            user_identity=user_identity,
        )
