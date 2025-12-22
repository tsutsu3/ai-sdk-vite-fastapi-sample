from pydantic import BaseModel, Field


class UserInfo(BaseModel, frozen=True):
    user_id: str
    email: str | None
    provider: str | None
    first_name: str | None
    last_name: str | None


class ToolOverrides(BaseModel, frozen=True):
    allow: list[str] = Field(default_factory=list)
    deny: list[str] = Field(default_factory=list)


class TenantDoc(BaseModel, frozen=True):
    id: str
    key: str
    name: str
    default_tools: list[str] = Field(default_factory=list)
    updated_at: str | None = None


class UserDoc(BaseModel, frozen=True):
    id: str
    tenant_id: str
    user_id: str | None = None
    email: str | None = None
    tool_overrides: ToolOverrides = Field(default_factory=ToolOverrides)
    first_name: str | None = None
    last_name: str | None = None
    updated_at: str | None = None


class TenantMemory(BaseModel, frozen=True):
    tenant_name: str
    default_tools: list[str] = Field(default_factory=list)


class UserMemory(BaseModel, frozen=True):
    tenant_id: str
    tool_overrides: ToolOverrides = Field(default_factory=ToolOverrides)
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None


class AuthzRecord(BaseModel, frozen=True):
    tenant_id: str
    tools: list[str]
    first_name: str | None
    last_name: str | None
    email: str | None


class AuthorizationResponse(BaseModel, frozen=True):
    user: UserInfo
    tools: list[str]
