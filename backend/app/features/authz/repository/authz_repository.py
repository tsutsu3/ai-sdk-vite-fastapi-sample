from typing import Protocol

from app.features.authz.models import AuthzRecord


class AuthzRepository(Protocol):
    async def get_authz(self, user_id: str) -> AuthzRecord | None:
        """Return authorization data for the provided user id."""
        raise NotImplementedError
