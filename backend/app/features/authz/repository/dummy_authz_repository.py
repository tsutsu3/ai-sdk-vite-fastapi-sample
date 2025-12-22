from app.features.authz.models import AuthzRecord
from app.features.authz.repository.authz_repository import AuthzRepository


class DummyAuthzRepository(AuthzRepository):
    async def get_authz(self, user_id: str) -> AuthzRecord | None:
        return AuthzRecord(
            tenant_id="default",
            tools=[],
            first_name="Demo",
            last_name="User",
            email="demo@example.com",
        )
