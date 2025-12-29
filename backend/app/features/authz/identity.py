from fastapi import Request

from app.features.authz.schemas import UserInfo


def parse_user_from_headers(request: Request) -> UserInfo:
    """Extract user identity from request headers.

    Falls back to an anonymous principal when no provider headers are found.

    Args:
        request: Incoming request.

    Returns:
        UserInfo: Parsed user identity.
    """
    headers = request.headers

    if request.app.state.app_config.auth_provider == "local":
        return UserInfo(
            id=request.app.state.app_config.local_auth_user_id,
            email=request.app.state.app_config.local_auth_user_email,
            provider="local",
            first_name=None,
            last_name=None,
        )

    if request.app.state.app_config.auth_provider == "easyauth":
        # Azure App Service EasyAuth
        easy_auth_id = headers.get("x-ms-client-principal-id")
        easy_auth_email = headers.get("x-ms-client-principal-name")

        if easy_auth_id:
            return UserInfo(
                id=easy_auth_id,
                email=easy_auth_email,
                provider="easyauth",
                first_name=None,
                last_name=None,
            )

    if request.app.state.app_config.auth_provider == "iap":
        # Google IAP
        iap_user = headers.get("x-goog-authenticated-user-id")
        iap_email = headers.get("x-goog-authenticated-user-email")
        if iap_user:
            # iap_user format: "accounts.google.com:userid"
            user_id = iap_user.split(":")[-1]
            email = iap_email.split(":")[-1] if iap_email else None
            return UserInfo(
                id=user_id,
                email=email,
                provider="iap",
                first_name=None,
                last_name=None,
            )

    if request.app.state.app_config.auth_provider == "none":
        return UserInfo(
            id="anonymous",
            email="jon.doe@example.com",
            provider="none",
            first_name="Jon",
            last_name="Doe",
        )

    # Fallback to anonymous user
    return UserInfo(
        id="anonymous",
        email="jon.doe@example.com",
        provider="none",
        first_name="Jon",
        last_name="Doe",
    )
