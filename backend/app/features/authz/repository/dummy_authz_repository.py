from app.features.authz.repository.authz_repository import AuthzRecord, AuthzRepository


class DummyAuthzRepository(AuthzRepository):
    def get_authz(self, user_id: str) -> AuthzRecord | None:
        return AuthzRecord(
            tools=[],
            first_name="Demo",
            last_name="User",
            email="demo@example.com",
        )
