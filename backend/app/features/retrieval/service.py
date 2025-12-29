from collections.abc import Sequence

from app.features.retrieval.providers.base import RetrievalProvider
from app.features.retrieval.schemas import RetrievalResult


class RetrievalService:
    """Service for resolving retrieval providers and executing searches.

    This service centralizes provider resolution and search execution so the
    API layer stays provider-agnostic and defaults are applied consistently.
    """

    def __init__(
        self, providers: dict[str, RetrievalProvider], default_provider: str = "memory"
    ) -> None:
        """Initialize the retrieval service.

        Args:
            providers: Provider registry keyed by provider id.
            default_provider: Default provider id.
        """
        self._providers = {key.lower(): provider for key, provider in providers.items()}
        self._default_provider = default_provider.lower()

    def resolve_provider(self, provider: str | None) -> RetrievalProvider | None:
        """Resolve a retrieval provider by id.

        Normalizes ids to improve compatibility with UI selections.

        Args:
            provider: Provider id or None.

        Returns:
            RetrievalProvider | None: Provider instance or None.
        """
        if provider:
            normalized = provider.strip().lower().replace(" ", "-").replace("_", "-")
            if normalized in self._providers:
                return self._providers[normalized]
        return self._providers.get(self._default_provider)

    async def search(
        self,
        query: str,
        data_source: str,
        provider: str | None,
        top_k: int = 5,
        *,
        query_embedding: list[float] | None = None,
    ) -> Sequence[RetrievalResult]:
        """Execute a retrieval search with the selected provider.

        Returns an empty list if no provider is available.

        Args:
            query: User query text.
            data_source: Data source identifier.
            provider: Provider id override.
            top_k: Maximum results to return.
            query_embedding: Optional embedding for the query.

        Returns:
            Sequence[RetrievalResult]: Search results.
        """
        impl = self.resolve_provider(provider)
        if not impl:
            return []
        return await impl.search(
            query,
            data_source,
            top_k,
            query_embedding=query_embedding,
        )
