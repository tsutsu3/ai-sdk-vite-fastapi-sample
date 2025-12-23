from pydantic import BaseModel, ConfigDict, Field


class ModelCapability(BaseModel):
    model_config = ConfigDict(populate_by_name=True, frozen=True)

    id: str
    name: str
    chef: str
    chef_slug: str = Field(alias="chefSlug")
    providers: list[str]


class WebSearchEngineCapability(BaseModel):
    model_config = ConfigDict(populate_by_name=True, frozen=True)

    id: str
    name: str


class CapabilitiesResponse(BaseModel, frozen=True):
    models: list[ModelCapability]
    web_search_engines: list[WebSearchEngineCapability] = Field(
        default_factory=list,
        alias="webSearchEngines",
    )
    default_web_search_engine: str | None = Field(
        default=None,
        alias="defaultWebSearchEngine",
    )
