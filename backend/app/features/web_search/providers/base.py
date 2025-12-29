from abc import ABC, abstractmethod
from collections.abc import Sequence

from app.features.web_search.models import WebSearchResult


class WebSearchProvider(ABC):
    """Abstract interface for web search providers.

    Implementations run search queries against external engines and normalize
    results into a common shape for downstream formatting.
    """

    id: str
    name: str

    @abstractmethod
    async def search(self, query: str, count: int = 5) -> Sequence[WebSearchResult]:
        """Execute a web search.

        The results should be ranked by relevance and ready for UI display
        or prompt injection.
        """
        raise NotImplementedError
