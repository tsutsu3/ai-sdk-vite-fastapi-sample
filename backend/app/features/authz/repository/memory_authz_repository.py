import asyncio
import random

from app.features.authz.models import (
    AuthzRecord,
    TenantMemory,
    ToolOverrides,
    UserMemory,
)
from app.features.authz.repository.authz_repository import AuthzRepository
from app.features.authz.repository.tool_merge import merge_tools


class MemoryAuthzRepository(AuthzRepository):
    def __init__(self) -> None:
        self._tenants: dict[str, TenantMemory] = {
            "tenant-demo": TenantMemory(
                tenant_name="demo",
                default_tools=["rag01", "rag02"],
            ),
            "tenant-rag01": TenantMemory(
                tenant_name="rag01",
                default_tools=["rag01"],
            ),
            "tenant-rag02": TenantMemory(
                tenant_name="rag02",
                default_tools=["rag02"],
            ),
        }
        self._users: dict[str, UserMemory] = {
            "8098fdsgsgrf": UserMemory(
                tenant_id="tenant-demo",
                tool_overrides=ToolOverrides(),
                first_name="Taro",
                last_name="Tanaka",
                email="tanaka.taro@example.com",
            ),
            "user-rag01": UserMemory(
                tenant_id="tenant-rag01",
                tool_overrides=ToolOverrides(),
                first_name="Jamie",
                last_name="Lee",
                email="jamie.lee@example.com",
            ),
            "user-rag02": UserMemory(
                tenant_id="tenant-rag02",
                tool_overrides=ToolOverrides(),
                first_name="Taylor",
                last_name="Kim",
                email="taylor.kim@example.com",
            ),
        }

    async def get_authz(self, user_id: str) -> AuthzRecord | None:
        user = self._users.get(user_id)
        if not user:
            return None
        await asyncio.sleep(random.random() * 2)
        tenant_id = user.tenant_id
        tenant = self._tenants.get(tenant_id)
        default_tools = tenant.default_tools if tenant else []
        overrides = user.tool_overrides
        tools = merge_tools(default_tools, overrides)
        return AuthzRecord(
            tenant_id=tenant_id,
            tools=tools,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
        )
