import argparse
import asyncio
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.core.config import Settings  # noqa: E402
from app.features.authz.models import (  # noqa: E402
    ProvisioningRecord,
    ProvisioningStatus,
    ToolOverridesRecord,
)
from app.infra.cosmos_client import CosmosClientProvider  # noqa: E402
from app.infra.persistence.factory_selector import (  # noqa: E402
    create_repository_factory,
)
from app.shared.time import now  # noqa: E402


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Provision a user into the provisioning container.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--email", required=True, help="User email address.")
    parser.add_argument("--tenant-id", required=True, help="Tenant identifier.")
    parser.add_argument("--first-name", required=True, help="User first name.")
    parser.add_argument("--last-name", required=True, help="User last name.")
    parser.add_argument(
        "--allow",
        default="",
        help="Comma-separated tool allow list.",
    )
    parser.add_argument(
        "--deny",
        default="",
        help="Comma-separated tool deny list.",
    )
    parser.add_argument(
        "--provisioning-id",
        default=None,
        help="Provisioning id (defaults to a new UUID).",
    )
    return parser.parse_args()


def _parse_list(value: str) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


async def _main() -> None:
    args = _parse_args()
    settings = Settings()
    app_config = settings.to_app_config()
    storage_caps = settings.to_storage_capabilities()

    cosmos_provider = None
    if storage_caps.db_backend == "azure":
        cosmos_provider = CosmosClientProvider(app_config)

    factory = create_repository_factory(
        app_config,
        storage_caps,
        cosmos_provider=cosmos_provider,
    )
    repo = factory.authz()

    timestamp = now()
    record = ProvisioningRecord(
        id=args.provisioning_id or str(uuid.uuid4()),
        email=args.email,
        tenant_id=args.tenant_id,
        first_name=args.first_name,
        last_name=args.last_name,
        tool_overrides=ToolOverridesRecord(
            allow=_parse_list(args.allow),
            deny=_parse_list(args.deny),
        ),
        status=ProvisioningStatus.PENDING,
        created_at=timestamp,
        updated_at=timestamp,
    )
    await repo.save_provisioning(record)

    if cosmos_provider:
        await cosmos_provider.close()


if __name__ == "__main__":
    asyncio.run(_main())
