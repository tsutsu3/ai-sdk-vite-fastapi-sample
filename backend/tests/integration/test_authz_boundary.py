from fastapi.testclient import TestClient

from app.core.application import create_app
from app.features.authz.models import (
    ProvisioningRecord,
    ProvisioningStatus,
    TenantRecord,
    UserIdentityRecord,
    UserRecord,
)
from app.features.authz.ports import AuthzRepository
from app.features.authz.service import AuthzService


class DenyAuthzRepository(AuthzRepository):
    async def get_user(self, user_id: str) -> UserRecord | None:
        return None

    async def get_tenant(self, tenant_id: str) -> TenantRecord | None:
        return None

    async def get_user_identity(self, identity_id: str) -> UserIdentityRecord | None:
        return None

    async def list_provisioning_by_email(
        self, email: str, status: ProvisioningStatus
    ) -> list[ProvisioningRecord]:
        return []

    async def save_user(self, record: UserRecord) -> None:
        return None

    async def save_user_identity(self, record: UserIdentityRecord) -> None:
        return None

    async def save_provisioning(self, record: ProvisioningRecord) -> None:
        return None


def test_request_context_requires_authz():
    app = create_app()
    with TestClient(app) as client:
        app.state.authz_repository = DenyAuthzRepository()
        app.state.authz_service = AuthzService(app.state.authz_repository)
        response = client.get("/api/conversations")
        assert response.status_code == 403
