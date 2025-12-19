from fastapi import APIRouter, Depends, Request

from app.dependencies import get_authz_repository
from app.features.authz.identity import parse_user_from_headers
from app.features.authz.models import AuthorizationResponse, UserInfo
from app.features.authz.repository.authz_repository import AuthzRepository

router = APIRouter()


@router.get("/api/authz", response_model=AuthorizationResponse)
def get_authorization(
    request: Request,
    repo: AuthzRepository = Depends(get_authz_repository),
) -> AuthorizationResponse:
    """
    Return access control for the current user.
    In production, this should query a NoSQL/AuthZ store using the user_id.
    """
    user = parse_user_from_headers(request)
    record = repo.get_authz(user.user_id)
    tools = record.tools if record else []

    return AuthorizationResponse(
        user=UserInfo(
            user_id=user.user_id,
            email=record.email if record else user.email,
            provider=user.provider,
            first_name=record.first_name if record else user.first_name,
            last_name=record.last_name if record else user.last_name,
        ),
        tools=tools,
    )
