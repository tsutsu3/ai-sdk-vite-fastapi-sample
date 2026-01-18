from pydantic import BaseModel, ConfigDict, Field

from app.features.authz.models import UserInfo


class TenantSummary(BaseModel):
    """Tenant summary for selection UI."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(description="Tenant id.", examples=["id-tenant001"])
    name: str = Field(description="Tenant name.", examples=["Tenant 001"])
    key: str | None = Field(default=None, description="Tenant key.", examples=["tenant-001"])


class ConfigResponse(BaseModel):
    """User configuration response payload."""

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    user: UserInfo = Field(description="Authenticated user profile.")
    tenant_ids: list[str] = Field(
        alias="tenantIds",
        description="Tenants the user can access.",
        examples=[["id-tenant001", "id-tenant002"]],
    )
    active_tenant_id: str = Field(
        alias="activeTenantId",
        description="Active tenant id used for requests.",
        examples=["id-tenant001"],
    )
    tenants: list[TenantSummary] = Field(
        default_factory=list,
        description="Tenant metadata for selection.",
    )


class ConfigUpdateRequest(BaseModel):
    """Request payload for updating the active tenant."""

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    active_tenant_id: str = Field(
        alias="activeTenantId",
        description="Tenant id to set as active.",
        examples=["id-tenant001"],
    )
