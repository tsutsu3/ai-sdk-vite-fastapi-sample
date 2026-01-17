from pydantic import BaseModel, ConfigDict, Field

from .models import ToolGroup, UserInfo


class AuthorizationResponse(BaseModel):
    """Authorization response payload."""

    model_config = ConfigDict(
        frozen=True,
        json_schema_extra={
            "examples": [
                {
                    "user": {
                        "id": "user-001",
                        "email": "local.user001@example.com",
                        "provider": "local",
                        "first_name": "Taro",
                        "last_name": "Yamada",
                    },
                    "tools": ["tool01", "tool02"],
                    "toolGroups": [
                        {
                            "id": "tool01",
                            "items": [{"id": "tool01"}],
                        }
                    ],
                }
            ]
        },
    )

    user: UserInfo = Field(description="Authenticated user profile.")
    tools: list[str] = Field(description="Allowed tool ids.")
    tool_groups: list[ToolGroup] = Field(
        default_factory=list,
        alias="toolGroups",
        description="Tool group metadata for UI.",
    )
