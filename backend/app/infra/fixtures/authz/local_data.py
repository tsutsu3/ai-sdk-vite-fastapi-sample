from app.features.authz.models import (
    MembershipRecord,
    MembershipStatus,
    TenantRecord,
    ToolOverridesRecord,
    UserIdentityRecord,
    UserRecord,
)

TENANTS: dict[str, TenantRecord] = {
    "id-tenant001": TenantRecord(
        id="id-tenant001",
        name="Tenant 001",
        default_tool_ids=[
            "tool0101",
            "tool0102",
            "tool0201",
            "tool0202",
            "tool0301",
            "tool0302",
        ],
    ),
    "id-tenant002": TenantRecord(
        id="id-tenant002",
        name="Tenant 002",
        default_tool_ids=[
            "tool0101",
            "tool0301",
            "tool0302",
        ],
    ),
    "id-tenant003": TenantRecord(
        id="id-tenant003",
        name="Tenant 003",
        default_tool_ids=[
            "tool0201",
            "tool0202",
            "tool0301",
        ],
    ),
    "id-tenant004": TenantRecord(
        id="id-tenant004",
        name="Tenant 004",
        default_tool_ids=[],
    ),
}

USERS: dict[str, UserRecord] = {
    "user-local-001": UserRecord(
        id="user-local-001",
        active_tenant_id="id-tenant001",
        email="local.user001@example.com",
        first_name="Taro",
        last_name="Ichiro",
    )
}

USER_IDENTITIES: dict[str, UserIdentityRecord] = {
    "local-user-001-01": UserIdentityRecord(
        id="local-user-001-01",
        provider="local",
        user_id="user-local-001",
    )
}

MEMBERSHIPS: dict[str, MembershipRecord] = {
    "member-user-local-001-tenant001": MembershipRecord(
        id="member-user-local-001-tenant001",
        tenant_id="id-tenant001",
        user_id="user-local-001",
        status=MembershipStatus.ACTIVE,
        tool_overrides=ToolOverridesRecord(),
    ),
    "member-user-local-001-tenant002": MembershipRecord(
        id="member-user-local-001-tenant002",
        tenant_id="id-tenant002",
        user_id="user-local-001",
        status=MembershipStatus.ACTIVE,
        tool_overrides=ToolOverridesRecord(),
    ),
    "member-user-local-001-tenant003": MembershipRecord(
        id="member-user-local-001-tenant003",
        tenant_id="id-tenant003",
        user_id="user-local-001",
        status=MembershipStatus.ACTIVE,
        tool_overrides=ToolOverridesRecord(),
    ),
    "prov-local-001-001": MembershipRecord(
        id="prov-local-001-001",
        tenant_id="id-tenant001",
        invite_email="local.user001@example.com",
        status=MembershipStatus.PENDING,
        tool_overrides=ToolOverridesRecord(),
    ),
    "prov-local-001-002": MembershipRecord(
        id="prov-local-001-002",
        tenant_id="id-tenant001",
        invite_email="local.user002@example.com",
        status=MembershipStatus.PENDING,
        tool_overrides=ToolOverridesRecord(
            deny=["tool0201", "tool0202"],
        ),
    ),
    "prov-local-002-001": MembershipRecord(
        id="prov-local-002-001",
        tenant_id="id-tenant002",
        invite_email="yamada.ichiro@example.com",
        status=MembershipStatus.PENDING,
        tool_overrides=ToolOverridesRecord(),
    ),
    "prov-local-002-002": MembershipRecord(
        id="prov-local-002-002",
        tenant_id="id-tenant002",
        invite_email="yamada.jiro@example.com",
        status=MembershipStatus.PENDING,
        tool_overrides=ToolOverridesRecord(
            allow=["tool0201", "tool0202"],
        ),
    ),
    "prov-local-002-003": MembershipRecord(
        id="prov-local-002-003",
        tenant_id="id-tenant002",
        invite_email="yamada.saburo@example.com",
        status=MembershipStatus.PENDING,
        tool_overrides=ToolOverridesRecord(
            deny=["tool0101", "tool0102"],
        ),
    ),
    "prov-local-003-001": MembershipRecord(
        id="prov-local-003-001",
        tenant_id="id-tenant003",
        invite_email="suzuki.ichiro@example.com",
        status=MembershipStatus.PENDING,
        tool_overrides=ToolOverridesRecord(),
    ),
    "prov-local-003-002": MembershipRecord(
        id="prov-local-003-002",
        tenant_id="id-tenant003",
        invite_email="suzuki.jiro@example.com",
        status=MembershipStatus.PENDING,
        tool_overrides=ToolOverridesRecord(
            allow=["tool0101"],
        ),
    ),
    "prov-local-003-003": MembershipRecord(
        id="prov-local-003-003",
        tenant_id="id-tenant003",
        invite_email="suzuki.saburo@example.com",
        status=MembershipStatus.PENDING,
        tool_overrides=ToolOverridesRecord(
            deny=["tool0201", "tool0202"],
        ),
    ),
    "prov-local-004-001": MembershipRecord(
        id="prov-local-004-001",
        tenant_id="id-tenant004",
        invite_email="kobayashi.ichiro@example.com",
        status=MembershipStatus.PENDING,
        tool_overrides=ToolOverridesRecord(),
    ),
    "prov-local-004-002": MembershipRecord(
        id="prov-local-004-002",
        tenant_id="id-tenant004",
        invite_email="kobayashi.jiro@example.com",
        status=MembershipStatus.PENDING,
        tool_overrides=ToolOverridesRecord(
            allow=["tool0201", "tool0202", "tool0301"],
        ),
    ),
    "prov-local-004-003": MembershipRecord(
        id="prov-local-004-003",
        tenant_id="id-tenant004",
        invite_email="kobayashi.saburo@example.com",
        status=MembershipStatus.PENDING,
        tool_overrides=ToolOverridesRecord(
            allow=["tool0101", "tool0201", "tool0301"],
        ),
    ),
    "prov-local-1234567890": MembershipRecord(
        id="prov-local-1234567890",
        tenant_id="id-tenant001",
        invite_email="tsutsumi.toshio@minebea-ss.com",
        status=MembershipStatus.PENDING,
        tool_overrides=ToolOverridesRecord(),
    ),
}
