from pydantic import BaseModel, ConfigDict


class WebSearchResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    title: str
    url: str
    snippet: str | None = None


class WebSearchEngine(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    name: str
