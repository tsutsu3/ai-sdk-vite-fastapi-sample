from abc import ABC, abstractmethod
from collections.abc import Sequence

from app.features.retrieval.schemas import RetrievalResult


class RetrievalProvider(ABC):
    """Abstract interface for retrieval providers.

    Implementations perform similarity search over a data source and are
    swapped in by provider id. This keeps retrieval logic independent of
    the backing store (memory, pgvector, external search, etc.).
    """

    id: str
    name: str

    @abstractmethod
    async def search(
        self,
        query: str,
        data_source: str,
        top_k: int = 5,
        *,
        query_embedding: list[float] | None = None,
    ) -> Sequence[RetrievalResult]:
        """Perform a similarity search against the provider.

        The query_embedding may be required for some providers and allows
        higher-quality similarity scoring when available.
        """
        raise NotImplementedError
