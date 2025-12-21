from fastapi import Request

from app.features.authz.identity import parse_user_from_headers


def get_tenant_id(request: Request) -> str:
    tenant_id = request.headers.get("x-tenant-id")
    return tenant_id.strip() if tenant_id else "default"


def get_user_id(request: Request) -> str:
    return parse_user_from_headers(request).user_id
