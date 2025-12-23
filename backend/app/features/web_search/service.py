from collections.abc import Sequence

from app.features.web_search.models import WebSearchEngine, WebSearchResult
from app.features.web_search.providers.base import WebSearchProvider


class WebSearchService:
    def __init__(
        self,
        providers: dict[str, WebSearchProvider],
        default_engine: str | None = None,
    ) -> None:
        self._providers = {key.lower(): provider for key, provider in providers.items()}
        if default_engine and default_engine.lower() in self._providers:
            self._default_engine = default_engine.lower()
        else:
            self._default_engine = next(iter(self._providers), None)

    @property
    def default_engine(self) -> str | None:
        return self._default_engine

    def available_engines(self) -> Sequence[WebSearchEngine]:
        return [
            WebSearchEngine(id=provider.id, name=provider.name)
            for provider in self._providers.values()
        ]

    def resolve_engine(self, engine: str | None) -> WebSearchProvider | None:
        if engine:
            provider = self._providers.get(engine.lower())
            if provider:
                return provider
        if self._default_engine:
            return self._providers.get(self._default_engine)
        return None

    async def search(
        self,
        query: str,
        *,
        engine: str | None = None,
        count: int = 5,
    ) -> Sequence[WebSearchResult]:
        provider = self.resolve_engine(engine)
        if not provider:
            return []
        return await provider.search(query, count=count)
