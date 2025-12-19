import random
import time

from app.features.authz.repository.authz_repository import (
    AuthzRecord,
    AuthzRepository,
)


class MemoryAuthzRepository(AuthzRepository):
    def __init__(self) -> None:
        self._authz_table = {
            "8098fdsgsgrf": {
                "tools": ["rag01", "rag02"],
                "first_name": "Taro",
                "last_name": "Tanaka",
                "email": "tanaka.taro@example.com",
            },
            "user-rag01": {
                "tools": ["rag01"],
                "first_name": "Jamie",
                "last_name": "Lee",
                "email": "jamie.lee@example.com",
            },
            "user-rag02": {
                "tools": ["rag02"],
                "first_name": "Taylor",
                "last_name": "Kim",
                "email": "taylor.kim@example.com",
            },
        }

    def get_authz(self, user_id: str) -> AuthzRecord | None:
        row = self._authz_table.get(user_id)
        if not row:
            return None
        time.sleep(random.random() * 2)
        return AuthzRecord(
            tools=row.get("tools", []),
            first_name=row.get("first_name"),
            last_name=row.get("last_name"),
            email=row.get("email"),
        )
