from collections.abc import Sequence

from app.features.retrieval.providers.base import RetrievalProvider
from app.features.retrieval.schemas import RetrievalResult


class MemoryRetrievalProvider(RetrievalProvider):
    id = "memory"
    name = "Memory (Dummy)"

    def __init__(self) -> None:
        self._documents: dict[str, list[RetrievalResult]] = {
            "rag01": [
                RetrievalResult(
                    text="RAG quickstart covers chunking and metadata.",
                    url="https://example.com/rag01/quickstart.pdf",
                    title="RAG Quickstart",
                    score=0.9,
                ),
                RetrievalResult(
                    text="Evaluation tips for retrieval quality.",
                    url="https://example.com/rag01/eval.md",
                    title="Retrieval Evaluation",
                    score=0.8,
                ),
            ],
            "rag02": [
                RetrievalResult(
                    text="Advanced indexing strategies for mixed media.",
                    url="https://example.com/rag02/indexing.md",
                    title="Indexing Strategies",
                    score=0.9,
                ),
                RetrievalResult(
                    text="Hybrid search patterns and reranking.",
                    url="https://example.com/rag02/hybrid.md",
                    title="Hybrid Search",
                    score=0.8,
                ),
            ],
        }

    async def search(
        self,
        query: str,
        data_source: str,
        top_k: int = 5,
        *,
        query_embedding: list[float] | None = None,
    ) -> Sequence[RetrievalResult]:
        items = self._documents.get(data_source, [])
        return items[:top_k]
