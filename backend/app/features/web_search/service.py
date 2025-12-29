from collections.abc import Sequence

from app.features.web_search.models import WebSearchEngineResult, WebSearchResult
from app.features.web_search.providers.base import WebSearchProvider


class WebSearchService:
    """Service for resolving web search providers and executing searches.

    This service normalizes engine selection and fallback behavior so the API
    can request searches without coupling to a specific provider.
    """

    def __init__(
        self,
        providers: dict[str, WebSearchProvider],
        default_engine: str | None = None,
    ) -> None:
        """Initialize the web search service.

        Args:
            providers: Providers keyed by engine id.
            default_engine: Optional default engine id.
        """
        self._providers = {key.lower(): provider for key, provider in providers.items()}
        if default_engine and default_engine.lower() in self._providers:
            self._default_engine = default_engine.lower()
        else:
            self._default_engine = next(iter(self._providers), None)

    @property
    def default_engine(self) -> str | None:
        """Return the default search engine id."""
        return self._default_engine

    def available_engines(self) -> Sequence[WebSearchEngineResult]:
        """List available web search engines.

        The list is derived from configured providers.

        Returns:
            Sequence[WebSearchEngineResult]: Available engines.
        """
        return [
            WebSearchEngineResult(id=provider.id, name=provider.name)
            for provider in self._providers.values()
        ]

    def resolve_engine(self, engine: str | None) -> WebSearchProvider | None:
        """Resolve a web search provider by id.

        Falls back to the configured default when possible.

        Args:
            engine: Engine id or None.

        Returns:
            WebSearchProvider | None: Provider instance or None.
        """
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
        """Execute a web search with the selected provider.

        Returns an empty list when no provider is available.

        Args:
            query: Search query string.
            engine: Engine id override.
            count: Maximum results.

        Returns:
            Sequence[WebSearchResult]: Search results.
        """
        provider = self.resolve_engine(engine)
        if not provider:
            return []
        return await provider.search(query, count=count)
