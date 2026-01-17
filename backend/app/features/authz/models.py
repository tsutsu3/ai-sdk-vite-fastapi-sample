from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class ProvisioningStatus(str, Enum):
    """Provisioning status enumeration."""

    PENDING = "pending"
    ACTIVE = "active"
    DEACTIVATED = "deactivated"
    FAILED = "failed"


class ToolItem(BaseModel):
    """Tool item definition."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(description="Tool id.", examples=["tool01"])


class ToolGroup(BaseModel):
    """Tool group definition with nested items."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(description="Tool group id.", examples=["tool01"])
    items: list[ToolItem] = Field(
        default_factory=list,
        description="Tools included in the group.",
    )


class UserInfo(BaseModel):
    """User identity information from the authn layer."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(description="User id.", examples=["user-001"])
    email: str | None = Field(
        description="User email.",
        examples=["local.user001@example.com"],
    )
    provider: str | None = Field(description="Auth provider.", examples=["local"])
    first_name: str | None = Field(description="First name.", examples=["Taro"])
    last_name: str | None = Field(description="Last name.", examples=["Yamada"])


class ToolOverridesRecord(BaseModel):
    """Tool allow/deny overrides stored for repository access."""

    model_config = ConfigDict(frozen=True)

    allow: list[str] = Field(default_factory=list)
    deny: list[str] = Field(default_factory=list)


class TenantRecord(BaseModel):
    """Tenant record stored in the repository."""

    model_config = ConfigDict(frozen=True)

    id: str  # pk
    key: str | None = None
    name: str
    default_tools: list[str] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class UserIdentityRecord(BaseModel):
    """User identity record stored in the repository."""

    model_config = ConfigDict(frozen=True)

    id: str  # pk: IAP, EasyAuth, etc. identity ID
    provider: str | None = None
    user_id: str
    tenant_id: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class UserRecord(BaseModel):
    """User record stored in the repository."""

    model_config = ConfigDict(frozen=True)

    tenant_id: str  # hierarchy partition key [tenant_id / id]
    id: str | None = None
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    tool_overrides: ToolOverridesRecord = Field(default_factory=ToolOverridesRecord)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ProvisioningRecord(BaseModel):
    """Provisioning record stored in the repository."""

    model_config = ConfigDict(frozen=True)

    id: str
    email: str  # pk
    tenant_id: str
    first_name: str
    last_name: str
    tool_overrides: ToolOverridesRecord = Field(default_factory=ToolOverridesRecord)
    status: ProvisioningStatus = ProvisioningStatus.PENDING
    created_at: datetime | None = None
    updated_at: datetime | None = None


class AuthzRecord(BaseModel):
    """Resolved authorization record for a user."""

    model_config = ConfigDict(frozen=True)

    tenant_id: str
    tools: list[str]
    first_name: str | None
    last_name: str | None
    email: str | None
