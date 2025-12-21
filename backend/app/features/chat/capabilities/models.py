from pydantic import BaseModel, ConfigDict, Field


class ModelCapability(BaseModel, frozen=True):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str
    chef: str
    chef_slug: str = Field(alias="chefSlug")
    providers: list[str]


class CapabilitiesResponse(BaseModel, frozen=True):
    models: list[ModelCapability]
