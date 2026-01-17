from collections.abc import Sequence

from langchain_core.documents import Document

from app.features.retrieval.schemas import RetrievalResult


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
        # Try both "url" and "source_url" for compatibility
        url = metadata.get("url") or metadata.get("source_url") or ""
        if not url:
            # Skip documents without URLs
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
