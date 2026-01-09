from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_core.vectorstores import VectorStore

from app.features.retrieval.schemas import RetrievalResult
from app.features.retrieval.service import RetrievalService


class RetrievalServiceRetriever(BaseRetriever):
    """LangChain retriever wrapper around the retrieval service."""

    def __init__(
        self,
        service: RetrievalService,
        *,
        data_source: str,
        provider: str | None,
        top_k: int,
        query_embedding: list[float] | None = None,
    ) -> None:
        super().__init__()
        self._service = service
        self._data_source = data_source
        self._provider = provider
        self._top_k = top_k
        self._query_embedding = query_embedding

    async def _aget_relevant_documents(self, query: str) -> list[Document]:
        results = await self._service.search(
            query,
            self._data_source,
            self._provider,
            self._top_k,
            query_embedding=self._query_embedding,
        )
        return results_to_documents(results)


class RetrievalVectorStore(VectorStore):
    """VectorStore facade for retrieval providers that accept query embeddings."""

    def __init__(
        self,
        service: RetrievalService,
        *,
        data_source: str,
        provider: str | None,
    ) -> None:
        self._service = service
        self._data_source = data_source
        self._provider = provider

    @property
    def embeddings(self):  # noqa: D401 - interface requirement
        """Return None because embeddings are supplied externally."""
        return None

    def add_texts(self, texts: Sequence[str], metadatas: Sequence[dict[str, Any]] | None = None):
        raise NotImplementedError("Retrieval providers are read-only.")

    async def aadd_texts(
        self, texts: Sequence[str], metadatas: Sequence[dict[str, Any]] | None = None
    ):
        raise NotImplementedError("Retrieval providers are read-only.")

    def similarity_search(self, query: str, k: int = 4, **kwargs: Any) -> list[Document]:
        raise NotImplementedError("Use similarity_search_by_vector for vector queries.")

    async def asimilarity_search(self, query: str, k: int = 4, **kwargs: Any) -> list[Document]:
        raise NotImplementedError("Use similarity_search_by_vector for vector queries.")

    def similarity_search_by_vector(
        self, embedding: list[float], k: int = 4, **kwargs: Any
    ) -> list[Document]:
        raise NotImplementedError("Use asimilarity_search_by_vector in async contexts.")

    async def asimilarity_search_by_vector(
        self, embedding: list[float], k: int = 4, **kwargs: Any
    ) -> list[Document]:
        results = await self._service.search(
            "",
            self._data_source,
            self._provider,
            k,
            query_embedding=embedding,
        )
        return results_to_documents(results)

    def from_texts(  # type: ignore[override]
        self, texts: Sequence[str], embedding, metadatas: Sequence[dict[str, Any]] | None = None
    ):
        raise NotImplementedError("Retrieval providers are read-only.")


def results_to_documents(results: Sequence[RetrievalResult]) -> list[Document]:
    return [
        Document(
            page_content=result.text,
            metadata={
                "url": result.url,
                "title": result.title,
                "score": result.score,
            },
        )
        for result in results
    ]


def documents_to_results(documents: Sequence[Document]) -> list[RetrievalResult]:
    converted: list[RetrievalResult] = []
    for doc in documents:
        metadata = doc.metadata or {}
        url = metadata.get("url") or ""
        if not url:
            continue
        converted.append(
            RetrievalResult(
                text=doc.page_content,
                url=str(url),
                title=metadata.get("title"),
                score=metadata.get("score"),
            )
        )
    return converted


async def retrieve_documents(
    service: RetrievalService,
    *,
    provider_id: str,
    data_source: str,
    query: str,
    top_k: int,
    query_embedding: list[float] | None = None,
) -> list[Document]:
    use_vector_store = query_embedding is not None and provider_id == "postgres"
    if use_vector_store:
        vector_store = RetrievalVectorStore(
            service,
            data_source=data_source,
            provider=provider_id,
        )
        return await vector_store.asimilarity_search_by_vector(query_embedding, k=top_k)

    retriever = RetrievalServiceRetriever(
        service,
        data_source=data_source,
        provider=provider_id,
        top_k=top_k,
        query_embedding=query_embedding,
    )
    return await retriever.ainvoke(query)
