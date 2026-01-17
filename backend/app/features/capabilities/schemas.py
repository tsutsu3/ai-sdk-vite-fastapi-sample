from pydantic import BaseModel, ConfigDict, Field


class ModelCapability(BaseModel):
    """Chat model capability metadata."""

    model_config = ConfigDict(populate_by_name=True, frozen=True)

    id: str = Field(description="Model id.", examples=["gpt-4o"])
    name: str = Field(description="Display name.", examples=["GPT-4o"])
    chef: str = Field(description="Provider label.", examples=["OpenAI"])
    chef_slug: str = Field(alias="chefSlug", description="Provider slug.", examples=["openai"])
    providers: list[str] = Field(
        description="Available providers.", examples=[["openai", "azure"]]
    )


class APIPageSizeCapability(BaseModel):
    """API page size capability metadata."""

    model_config = ConfigDict(frozen=True)

    messages_page_size_default: int = Field(
        alias="messagesPageSizeDefault",
        description="Default messages page size.",
        examples=[30],
    )
    messages_page_size_max: int = Field(
        alias="messagesPageSizeMax",
        description="Max messages page size.",
        examples=[200],
    )
    conversations_page_size_default: int = Field(
        alias="conversationsPageSizeDefault",
        description="Default conversations page size.",
        examples=[50],
    )
    conversations_page_size_max: int = Field(
        alias="conversationsPageSizeMax",
        description="Max conversations page size.",
        examples=[200],
    )


class CapabilitiesResponse(BaseModel):
    """Capabilities response payload."""

    model_config = ConfigDict(
        frozen=True,
        json_schema_extra={
            "examples": [
                {
                    "models": [
                        {
                            "id": "gpt-4o",
                            "name": "GPT-4o",
                            "chef": "OpenAI",
                            "chefSlug": "openai",
                            "providers": ["openai", "azure"],
                        }
                    ],
                    "defaultModel": "gpt-4o",
                    "apiPageSizes": {
                        "messagesPageSizeDefault": 30,
                        "messagesPageSizeMax": 200,
                        "conversationsPageSizeDefault": 50,
                        "conversationsPageSizeMax": 200,
                    },
                }
            ]
        },
    )

    models: list[ModelCapability] = Field(description="Available chat models.")
    default_model: str = Field(
        default="",
        alias="defaultModel",
        description="Default model id.",
        examples=["gpt-4o"],
    )
    api_page_sizes: APIPageSizeCapability = Field(
        alias="apiPageSizes",
        description="API paging defaults and limits.",
    )
