"""Provision a user into the authorization system.

This script provisions a user into the authorization system for the application.
It creates a provisioning record for a user, including email, tenant, name, and tool access overrides,
and saves it to the backend database (e.g., Azure Cosmos DB if configured).

Usage:
    python scripts/provision_user.py --email <email> --tenant-id <tenant> --first-name <first> --last-name <last> [--allow <tools>] [--deny <tools>] [--provisioning-id <id>]
    python scripts/provision_user.py --csv <path> [--allow <tools>] [--deny <tools>]

Arguments:
    --email           User email address (required)
    --tenant-id       Tenant identifier (required)
    --first-name      User first name (required)
    --last-name       User last name (required)
    --allow           Comma-separated tool allow list (optional)
    --deny            Comma-separated tool deny list (optional)
    --provisioning-id Provisioning record ID (optional, defaults to new UUID)
    --csv             CSV file with provisioning records (optional)

CSV headers:
    email, tenant_id, first_name, last_name, allow, deny, provisioning_id

This script must be run from the project root or a location where the backend/app directory is accessible.
"""

import argparse
import asyncio
import csv
import sys
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parent / "backend" / "app"
sys.path.insert(0, str(ROOT))

from app.core.config import Settings  # noqa: E402
from app.features.authz.models import (  # noqa: E402
    ProvisioningRecord,
    ProvisioningStatus,
    ToolOverridesRecord,
)
from app.infra.client.cosmos_client import CosmosClientProvider  # noqa: E402
from app.infra.client.firestore_client import FirestoreClientProvider  # noqa: E402
from app.infra.persistence.factory_selector import (  # noqa: E402
    create_repository_factory,
)
from app.shared.time import now  # noqa: E402


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Provision a user into the provisioning container.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--email", help="User email address.")
    parser.add_argument("--tenant-id", help="Tenant identifier.")
    parser.add_argument("--first-name", help="User first name.")
    parser.add_argument("--last-name", help="User last name.")
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
    parser.add_argument(
        "--csv",
        default=None,
        help="CSV file with provisioning records.",
    )
    return parser.parse_args()


def _parse_list(value: str) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _resolve_value(value: str | None) -> str:
    return value.strip() if isinstance(value, str) else ""


def _load_csv(path: str) -> list[dict[str, str]]:
    with open(path, "r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows: list[dict[str, str]] = []
        for row in reader:
            if not row:
                continue
            rows.append({key: _resolve_value(value) for key, value in row.items()})
        return rows


async def _create_repo(settings: Settings):
    app_config = settings.to_app_config()
    storage_caps = settings.to_storage_capabilities()
    cosmos_provider = None
    firestore_provider = None

    if storage_caps.db_backend == "azure":
        cosmos_provider = CosmosClientProvider(app_config)
    elif storage_caps.db_backend == "gcp":
        firestore_provider = FirestoreClientProvider(app_config)

    factory = create_repository_factory(
        app_config,
        storage_caps,
        cosmos_provider=cosmos_provider,
        firestore_provider=firestore_provider,
    )
    return await factory.authz(), cosmos_provider or firestore_provider


def _build_record(
    *,
    email: str,
    tenant_id: str,
    first_name: str,
    last_name: str,
    allow: list[str],
    deny: list[str],
    provisioning_id: str | None,
    timestamp: str,
) -> ProvisioningRecord:
    return ProvisioningRecord(
        id=provisioning_id or str(uuid.uuid4()),
        email=email,
        tenant_id=tenant_id,
        first_name=first_name,
        last_name=last_name,
        tool_overrides=ToolOverridesRecord(allow=allow, deny=deny),
        status=ProvisioningStatus.PENDING,
        created_at=timestamp,
        updated_at=timestamp,
    )


async def _provision_from_csv(args: argparse.Namespace, repo) -> None:
    rows = _load_csv(args.csv)
    if not rows:
        raise SystemExit("CSV file has no rows to process.")
    default_allow = _parse_list(args.allow)
    default_deny = _parse_list(args.deny)
    timestamp = now()

    for row in rows:
        email = row.get("email", "")
        tenant_id = row.get("tenant_id", "")
        first_name = row.get("first_name", "")
        last_name = row.get("last_name", "")
        if not (email and tenant_id and first_name and last_name):
            print(f"Skipping row with missing fields: {row}", file=sys.stderr)
            continue

        record = _build_record(
            email=email,
            tenant_id=tenant_id,
            first_name=first_name,
            last_name=last_name,
            allow=_parse_list(row.get("allow")) or default_allow,
            deny=_parse_list(row.get("deny")) or default_deny,
            provisioning_id=row.get("provisioning_id") or None,
            timestamp=timestamp,
        )
        await repo.save_provisioning(record)
        print(f"✓ Provisioned user: {record.id} ({record.email})")


async def _provision_single(args: argparse.Namespace, repo) -> None:
    if not (args.email and args.tenant_id and args.first_name and args.last_name):
        raise SystemExit("Missing required args: --email --tenant-id --first-name --last-name")

    record = _build_record(
        email=args.email,
        tenant_id=args.tenant_id,
        first_name=args.first_name,
        last_name=args.last_name,
        allow=_parse_list(args.allow),
        deny=_parse_list(args.deny),
        provisioning_id=args.provisioning_id,
        timestamp=now(),
    )
    await repo.save_provisioning(record)
    print(f"✓ Provisioned user: {record.email} ({record.tenant_id})")


async def _main() -> None:
    args = _parse_args()
    settings = Settings()
    repo, provider = await _create_repo(settings)

    print(f"DB_BACKEND: {settings.db_backend.name}")
    print(f"DB: {provider}")
    print(f"REPO: {repo}")

    try:
        if args.csv:
            await _provision_from_csv(args, repo)
        else:
            await _provision_single(args, repo)
    finally:
        if provider:
            await provider.close()


if __name__ == "__main__":
    print("Starting user provisioning script...")

    asyncio.run(_main())

    print("User provisioning script completed.")
