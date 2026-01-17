from app.features.authz.models import (
    ProvisioningRecord,
    TenantRecord,
    ToolOverridesRecord,
    UserIdentityRecord,
    UserRecord,
)

TENANTS: dict[str, TenantRecord] = {
    "id-tenant001": TenantRecord(
        id="id-tenant001",
        name="Tenant 001",
        default_tools=["tool01", "tool02", "tool03"],
    ),
    "id-tenant002": TenantRecord(
        id="id-tenant002",
        name="Tenant 002",
        default_tools=["tool01", "tool03"],
    ),
    "id-tenant003": TenantRecord(
        id="id-tenant003",
        name="Tenant 003",
        default_tools=["tool02", "tool03"],
    ),
    "id-tenant004": TenantRecord(
        id="id-tenant004",
        name="Tenant 004",
        default_tools=[],
    ),
}

USERS: dict[str, UserRecord] = {}

USER_IDENTITIES: dict[str, UserIdentityRecord] = {}

PROVISIONING: dict[str, ProvisioningRecord] = {
    "prov-local-001-001": ProvisioningRecord(
        id="prov-local-001-001",
        email="local.user001@example.com",
        tenant_id="id-tenant001",
        first_name="Taro",
        last_name="Ichiro",
        tool_overrides=ToolOverridesRecord(),
    ),
    "prov-local-001-002": ProvisioningRecord(
        id="prov-local-001-002",
        email="local.user002@example.com",
        tenant_id="id-tenant001",
        first_name="Keiko",
        last_name="Tanaka",
        tool_overrides=ToolOverridesRecord(
            deny=["tool02"],
        ),
    ),
    "prov-local-002-001": ProvisioningRecord(
        id="prov-local-002-001",
        email="yamada.ichiro@example.com",
        tenant_id="id-tenant002",
        first_name="Ichiro",
        last_name="Yamada",
        tool_overrides=ToolOverridesRecord(),
    ),
    "prov-local-002-002": ProvisioningRecord(
        id="prov-local-002-002",
        email="yamada.jiro@example.com",
        tenant_id="id-tenant002",
        first_name="Jiro",
        last_name="Yamada",
        tool_overrides=ToolOverridesRecord(
            allow=["tool02", "tool03"],
        ),
    ),
    "prov-local-002-003": ProvisioningRecord(
        id="prov-local-002-003",
        email="yamada.saburo@example.com",
        tenant_id="id-tenant002",
        first_name="Saburo",
        last_name="Yamada",
        tool_overrides=ToolOverridesRecord(
            deny=["tool01"],
        ),
    ),
    "prov-local-003-001": ProvisioningRecord(
        id="prov-local-003-001",
        email="suzuki.ichiro@example.com",
        tenant_id="id-tenant003",
        first_name="Ichiro",
        last_name="Suzuki",
        tool_overrides=ToolOverridesRecord(),
    ),
    "prov-local-003-002": ProvisioningRecord(
        id="prov-local-003-002",
        email="suzuki.jiro@example.com",
        tenant_id="id-tenant003",
        first_name="Jiro",
        last_name="Suzuki",
        tool_overrides=ToolOverridesRecord(
            allow=["tool01"],
        ),
    ),
    "prov-local-003-003": ProvisioningRecord(
        id="prov-local-003-003",
        email="suzuki.saburo@example.com",
        tenant_id="id-tenant003",
        first_name="Saburo",
        last_name="Suzuki",
        tool_overrides=ToolOverridesRecord(
            deny=["tool02"],
        ),
    ),
    "prov-local-004-001": ProvisioningRecord(
        id="prov-local-004-001",
        email="kobayashi.ichiro@example.com",
        tenant_id="id-tenant004",
        first_name="Ichiro",
        last_name="Kobayashi",
        tool_overrides=ToolOverridesRecord(),
    ),
    "prov-local-004-002": ProvisioningRecord(
        id="prov-local-004-002",
        email="kobayashi.jiro@example.com",
        tenant_id="id-tenant004",
        first_name="Jiro",
        last_name="Kobayashi",
        tool_overrides=ToolOverridesRecord(
            allow=["tool02", "tool03"],
        ),
    ),
    "prov-local-004-003": ProvisioningRecord(
        id="prov-local-004-003",
        email="kobayashi.saburo@example.com",
        tenant_id="id-tenant004",
        first_name="Saburo",
        last_name="Kobayashi",
        tool_overrides=ToolOverridesRecord(
            allow=["tool01", "tool02", "tool03"],
        ),
    ),
    "prov-local-1234567890": ProvisioningRecord(
        id="1234567890",
        email="tsutsumi.toshio@minebea-ss.com",
        tenant_id="id-tenant001",
        first_name="Tsutsumi",
        last_name="Toshio",
        tool_overrides=ToolOverridesRecord(),
    ),
}
