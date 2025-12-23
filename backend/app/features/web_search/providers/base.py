from abc import ABC, abstractmethod
from collections.abc import Sequence

from app.features.web_search.models import WebSearchResult


class WebSearchProvider(ABC):
    id: str
    name: str

    @abstractmethod
    async def search(self, query: str, count: int = 5) -> Sequence[WebSearchResult]:
        raise NotImplementedError
