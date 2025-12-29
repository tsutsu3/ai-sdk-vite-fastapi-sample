from pydantic import BaseModel, ConfigDict


class WebSearchResult(BaseModel):
    """Web search result item."""

    model_config = ConfigDict(frozen=True)

    title: str
    url: str
    snippet: str | None = None


class WebSearchEngineResult(BaseModel):
    """Web search engine descriptor."""

    model_config = ConfigDict(frozen=True)

    id: str
    name: str
