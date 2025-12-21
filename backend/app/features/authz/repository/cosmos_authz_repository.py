from app.core.config import AppConfig
from app.features.authz.repository.authz_repository import AuthzRecord, AuthzRepository
from app.shared.infra.cosmos_client import get_cosmos_container


def authz_partition(user_id: str) -> str:
    return user_id


class CosmosAuthzRepository(AuthzRepository):
    def __init__(self, config: AppConfig) -> None:
        self._container = get_cosmos_container(config, config.cosmos_authz_container)

    async def get_authz(self, user_id: str) -> AuthzRecord | None:
        pk = authz_partition(user_id)
        try:
            item = await self._container.read_item(item=user_id, partition_key=pk)
        except Exception:
            return None
        tenant_id = item.get("tenant_id") or item.get("tenantId")
        if not tenant_id:
            return None
        return AuthzRecord(
            tenant_id=tenant_id,
            tools=item.get("tools", []),
            first_name=item.get("first_name"),
            last_name=item.get("last_name"),
            email=item.get("email"),
        )
