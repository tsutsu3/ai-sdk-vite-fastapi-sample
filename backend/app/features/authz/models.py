from pydantic import BaseModel


class UserInfo(BaseModel, frozen=True):
    user_id: str
    email: str | None
    provider: str | None
    first_name: str | None
    last_name: str | None


class AuthorizationResponse(BaseModel, frozen=True):
    user: UserInfo
    tools: list[str]
