from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class AuthzRecord:
    tools: list[str]
    first_name: str | None
    last_name: str | None
    email: str | None


class AuthzRepository(Protocol):
    def get_authz(self, user_id: str) -> AuthzRecord | None:
        """Return authorization data for the provided user id."""
        raise NotImplementedError
