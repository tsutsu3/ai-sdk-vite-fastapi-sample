"""Provision tenant data into the authorization database.

This script provisions tenant records into Firestore or Azure Cosmos DB
for the authorization system. It helps bootstrap the authz database with
tenant and default tool configurations.

Usage:
    python scripts/provision_authz_db.py --tenant-id <id> --tenant-name <name> [--tools <tools>]
    python scripts/provision_authz_db.py --csv <path> [--tools <tools>]

Arguments:
    --tenant-id     Tenant identifier (required for single tenant)
    --tenant-name   Tenant name (required for single tenant)
    --tools         Comma-separated list of default tools (optional)
    --csv           CSV file with tenant records (optional)

CSV headers:
    tenant_id, tenant_name, default_tools

This script must be run from the project root or a location where the backend/app directory is accessible.
"""

import argparse
import asyncio
import uuid
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "backend" / "app"
sys.path.insert(0, str(ROOT))

from app.core.config import Settings  # noqa: E402
from app.features.authz.models import TenantRecord  # noqa: E402
from app.infra.client.cosmos_client import CosmosClientProvider  # noqa: E402
from app.infra.client.firestore_client import FirestoreClientProvider  # noqa: E402
from app.infra.persistence.factory_selector import (  # noqa: E402
    create_repository_factory,
)
from app.shared.time import now_datetime  # noqa: E402


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Provision tenant data into the authorization database.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--tenant-key", default=None, help="Tenant key.")
    parser.add_argument(
        "--tenant-id",
        default=None,
        help="Tenant identifier.",
    )
    parser.add_argument(
        "--tenant-name",
        default=None,
        help="Tenant name.",
    )
    parser.add_argument(
        "--tools",
        default="",
        help="Comma-separated list of default tools.",
    )
    parser.add_argument(
        "--csv",
        default=None,
        help="CSV file with tenant records.",
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

    if storage_caps.db_backend == "gcp":
        repo = await factory.authz()
    else:
        repo = factory.authz()

    return repo, cosmos_provider or firestore_provider


def _build_record(
    *,
    tenant_id: str | None,
    tenant_key: str,
    tenant_name: str,
    default_tools: list[str],
    timestamp,
) -> TenantRecord:
    return TenantRecord(
        id=tenant_id or str(uuid.uuid4()),
        key=tenant_key,
        name=tenant_name,
        default_tools=default_tools,
        created_at=timestamp,
        updated_at=timestamp,
    )


async def _provision_from_csv(args: argparse.Namespace, repo) -> None:
    rows = _load_csv(args.csv)
    if not rows:
        raise SystemExit("CSV file has no rows to process.")
    default_tools = _parse_list(args.tools)
    timestamp = now_datetime()

    for row in rows:
        tenant_id = row.get("tenant_id", None)
        tenant_key = row.get("tenant_key", "")
        tenant_name = row.get("tenant_name", "")
        if not (tenant_key and tenant_name):
            print(f"Skipping row with missing tenant_id or tenant_name: {row}", file=sys.stderr)
            continue

        tools = _parse_list(row.get("default_tools", "")) or default_tools
        record = _build_record(
            tenant_id=tenant_id,
            tenant_key=tenant_key,
            tenant_name=tenant_name,
            default_tools=tools,
            timestamp=timestamp,
        )
        await repo.save_tenant(record)
        print(f"✓ Provisioned tenant: {record.id} ({record.name})")


async def _provision_single(args: argparse.Namespace, repo) -> None:
    if not (args.tenant_key and args.tenant_name):
        raise SystemExit("Missing required args: --tenant-key --tenant-name")

    record = _build_record(
        tenant_id=args.tenant_id,
        tenant_key=args.tenant_key,
        tenant_name=args.tenant_name,
        default_tools=_parse_list(args.tools),
        timestamp=now_datetime(),
    )
    await repo.save_tenant(record)
    print(f"✓ Provisioned tenant: {record.id} ({record.name})")


async def _main() -> None:
    args = _parse_args()
    settings = Settings()
    repo, provider = await _create_repo(settings)

    print(f"DB_BACKEND: {settings.db_backend.name}")
    print(f"DB: {provider}")

    try:
        if args.csv:
            await _provision_from_csv(args, repo)
        else:
            await _provision_single(args, repo)
    finally:
        if provider:
            await provider.close()


if __name__ == "__main__":
    print("Starting authorization DB provisioning script...")

    asyncio.run(_main())

    print("Provisioning completed.")
