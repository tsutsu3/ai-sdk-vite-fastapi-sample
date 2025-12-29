from pydantic import BaseModel, ConfigDict, Field

from .models import ToolGroup, UserInfo


class AuthorizationResponse(BaseModel):
    """Authorization response payload."""

    model_config = ConfigDict(frozen=True)

    user: UserInfo
    tools: list[str]
    tool_groups: list[ToolGroup] = Field(default_factory=list, alias="toolGroups")
