import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.features.authz.models import ProvisioningStatus
from app.shared.time import now


class ToolOverridesDoc(BaseModel):
    """Tool allow/deny overrides for a user."""

    model_config = ConfigDict(frozen=True)

    allow: list[str] = Field(default_factory=list)
    deny: list[str] = Field(default_factory=list)


class ProvisioningDoc(BaseModel):
    """Provisioning document representation."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))  # Provisioning ID
    email: str
    tenant_id: str
    first_name: str
    last_name: str
    tool_overrides: ToolOverridesDoc = Field(default_factory=ToolOverridesDoc)
    status: ProvisioningStatus = ProvisioningStatus.PENDING
    created_at: str = Field(default_factory=now)
    updated_at: str = Field(default_factory=now)


class UserIdentityDoc(BaseModel):
    """User identity document representation."""

    model_config = ConfigDict(frozen=True)

    id: str  # IAP, EasyAuth, etc. identity ID
    provider: str | None = None  # Identity provider name
    user_id: str  # Internal user ID
    tenant_id: str
    created_at: str = Field(default_factory=now)
    updated_at: str = Field(default_factory=now)


class TenantDoc(BaseModel):
    """Tenant document representation."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    key: str | None = None  # Tenant identifier key
    name: str  # Tenant name
    default_tools: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=now)
    updated_at: str = Field(default_factory=now)


class UserDoc(BaseModel):
    """User document representation."""

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    id: str  # Internal user ID
    tenant_id: str
    user_id: str | None = Field(default=None, alias="userId")
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    tool_overrides: ToolOverridesDoc = Field(default_factory=ToolOverridesDoc)
    created_at: str = Field(default_factory=now)
    updated_at: str = Field(default_factory=now)
