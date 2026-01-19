from fastapi.testclient import TestClient

from app.core.application import create_app
from app.features.authz.models import (
    MembershipRecord,
    MembershipStatus,
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

    async def list_memberships_by_email(
        self, email: str, status: MembershipStatus
    ) -> list[MembershipRecord]:
        return []

    async def list_memberships_by_user(self, user_id: str) -> list[MembershipRecord]:
        return []

    async def get_membership_for_user(
        self, tenant_id: str, user_id: str
    ) -> MembershipRecord | None:
        return None

    async def save_user(self, record: UserRecord) -> None:
        return None

    async def save_user_identity(self, record: UserIdentityRecord) -> None:
        return None

    async def save_membership(self, record: MembershipRecord) -> None:
        return None

    async def save_tenant(self, record: TenantRecord) -> None:
        return None


def test_request_context_requires_authz():
    app = create_app()
    with TestClient(app) as client:
        app.state.authz_repository = DenyAuthzRepository()
        app.state.authz_service = AuthzService(app.state.authz_repository)
        response = client.get("/api/conversations")
        assert response.status_code == 403


def test_authz_endpoint_requires_authz():
    app = create_app()
    with TestClient(app) as client:
        app.state.authz_repository = DenyAuthzRepository()
        app.state.authz_service = AuthzService(app.state.authz_repository)
        response = client.get("/api/authz")
        assert response.status_code == 403


def test_messages_endpoint_requires_authz():
    app = create_app()
    with TestClient(app) as client:
        app.state.authz_repository = DenyAuthzRepository()
        app.state.authz_service = AuthzService(app.state.authz_repository)
        response = client.get("/api/conversations/conv-quickstart/messages")
        assert response.status_code == 403
