from fastapi import Request

from app.features.authz.models import UserInfo


def parse_user_from_headers(request: Request) -> UserInfo:
    """
    Extract user identity from EasyAuth or IAP headers.
    Falls back to an anonymous principal.
    """
    headers = request.headers

    # Azure App Service EasyAuth
    easy_auth_id = headers.get("x-ms-client-principal-id")
    easy_auth_email = headers.get("x-ms-client-principal-name")
    # TODO: dummy data
    easy_auth_id = "8098fdsgsgrf"
    easy_auth_email = "tanaka.taro@example.com"

    if easy_auth_id:
        return UserInfo(
            user_id=easy_auth_id,
            email=easy_auth_email,
            provider="easyauth",
            first_name=None,
            last_name=None,
        )

    # Google IAP
    iap_user = headers.get("x-goog-authenticated-user-id")
    iap_email = headers.get("x-goog-authenticated-user-email")
    if iap_user:
        # iap_user format: "accounts.google.com:userid"
        user_id = iap_user.split(":")[-1]
        email = iap_email.split(":")[-1] if iap_email else None
        return UserInfo(
            user_id=user_id,
            email=email,
            provider="iap",
            first_name=None,
            last_name=None,
        )

    return UserInfo(
        user_id="anonymous",
        email=None,
        provider="unknown",
        first_name=None,
        last_name=None,
    )
