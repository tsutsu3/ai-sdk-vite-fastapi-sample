from app.core.config import AppConfig
from app.features.authz.models import AuthzRecord, TenantDoc, ToolOverrides, UserDoc
from app.features.authz.repository.authz_repository import AuthzRepository
from app.features.authz.repository.tool_merge import merge_tools
from app.shared.infra.cosmos_client import get_cosmos_container


def authz_partition(user_id: str) -> str:
    return user_id


class CosmosAuthzRepository(AuthzRepository):
    def __init__(self, config: AppConfig) -> None:
        self._container = get_cosmos_container(config, config.cosmos_authz_container)

    async def get_authz(self, user_id: str) -> AuthzRecord | None:
        user = await self._read_user_item(user_id)
        if not user:
            return None
        tenant_id = user.get("tenant_id")
        if not tenant_id:
            return None
        tenant = await self._read_tenant_item(tenant_id)
        default_tools = tenant.default_tools if tenant else []
        overrides = user.tool_overrides if user.tool_overrides else ToolOverrides()
        tools = merge_tools(default_tools, overrides)
        return AuthzRecord(
            tenant_id=tenant_id,
            tools=tools,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
        )

    async def _read_user_item(self, user_id: str) -> UserDoc | None:
        items = self._container.query_items(
            query="SELECT * FROM c WHERE c.user_id = @user_id",
            parameters=[{"name": "@user_id", "value": user_id}],
            enable_cross_partition_query=True,
        )
        async for item in items:
            try:
                return UserDoc.model_validate(item)
            except Exception:
                return None
        return None

    async def _read_tenant_item(self, tenant_id: str) -> TenantDoc | None:
        items = self._container.query_items(
            query="SELECT * FROM c WHERE c.id = @tenant_id",
            parameters=[{"name": "@tenant_id", "value": tenant_id}],
            enable_cross_partition_query=True,
        )
        async for item in items:
            try:
                return TenantDoc.model_validate(item)
            except Exception:
                return None
        return None
