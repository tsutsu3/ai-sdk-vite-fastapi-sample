from pydantic import BaseModel, ConfigDict, Field


class ModelCapability(BaseModel):
    """Chat model capability metadata."""

    model_config = ConfigDict(populate_by_name=True, frozen=True)

    id: str
    name: str
    chef: str
    chef_slug: str = Field(alias="chefSlug")
    providers: list[str]


class WebSearchEngineCapability(BaseModel):
    """Web search engine capability metadata."""

    model_config = ConfigDict(populate_by_name=True, frozen=True)

    id: str
    name: str


class APIPageSizeCapability(BaseModel):
    """API page size capability metadata."""

    model_config = ConfigDict(frozen=True)

    messages_page_size_default: int = Field(alias="messagesPageSizeDefault")
    messages_page_size_max: int = Field(alias="messagesPageSizeMax")
    conversations_page_size_default: int = Field(alias="conversationsPageSizeDefault")
    conversations_page_size_max: int = Field(alias="conversationsPageSizeMax")


class CapabilitiesResponse(BaseModel):
    """Capabilities response payload."""

    model_config = ConfigDict(frozen=True)

    models: list[ModelCapability]
    default_model: str = Field(default="", alias="defaultModel")
    web_search_engines: list[WebSearchEngineCapability] = Field(
        default_factory=list,
        alias="webSearchEngines",
    )
    default_web_search_engine: str | None = Field(
        default=None,
        alias="defaultWebSearchEngine",
    )
    api_page_sizes: APIPageSizeCapability = Field(
        alias="apiPageSizes",
    )
