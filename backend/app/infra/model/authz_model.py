import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.features.authz.models import MembershipStatus
from app.shared.time import now


class ToolOverridesDoc(BaseModel):
    """Tool allow/deny overrides for a user."""

    model_config = ConfigDict(frozen=True)

    allow: list[str] = Field(default_factory=list)
    deny: list[str] = Field(default_factory=list)


class UserIdentityDoc(BaseModel):
    """User identity document representation."""

    model_config = ConfigDict(frozen=True)

    id: str  # IAP, EasyAuth, etc. identity ID
    provider: str | None = None  # Identity provider name
    user_id: str  # Internal user ID
    created_at: str = Field(default_factory=now)
    updated_at: str = Field(default_factory=now)


class TenantDoc(BaseModel):
    """Tenant document representation."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    key: str | None = None  # Tenant identifier key
    name: str  # Tenant name
    default_tool_ids: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=now)
    updated_at: str = Field(default_factory=now)


class UserDoc(BaseModel):
    """User document representation."""

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    id: str  # UserIdentityDoc.user_id
    active_tenant_id: str | None = None
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    created_at: str = Field(default_factory=now)
    updated_at: str = Field(default_factory=now)


class MembershipDoc(BaseModel):
    """Membership document representation."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    user_id: str | None = None
    invite_email: str | None = None
    role: str | None = None
    tool_overrides: ToolOverridesDoc = Field(default_factory=ToolOverridesDoc)
    status: MembershipStatus = MembershipStatus.PENDING
    created_at: str = Field(default_factory=now)
    updated_at: str = Field(default_factory=now)
