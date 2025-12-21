from app.features.authz.repository.authz_repository import AuthzRecord, AuthzRepository


class DummyAuthzRepository(AuthzRepository):
    async def get_authz(self, tenant_id: str, user_id: str) -> AuthzRecord | None:
        return AuthzRecord(
            tools=[],
            first_name="Demo",
            last_name="User",
            email="demo@example.com",
        )
