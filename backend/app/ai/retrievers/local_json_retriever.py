import json
import re
from logging import getLogger
from pathlib import Path
from typing import Any

from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from pydantic import Field

logger = getLogger(__name__)


class LocalJSONRetriever(BaseRetriever):
    """Local retriever that loads documents from JSON files with fuzzy matching.

    Supports:
    - JSON-based document storage
    - Fuzzy text matching (partial matches)
    - Case-insensitive search
    - English text only
    """

    json_path: Path = Field(description="Path to JSON file with documents array")
    k: int = Field(default=4, description="Number of results to return")
    min_score: float = Field(default=0.0, description="Minimum relevance score threshold")

    def _load_documents(self) -> list[dict[str, Any]]:
        """Load documents from JSON file.

        Returns:
            List of document dictionaries.
        """
        # Resolve to absolute path
        resolved_path = self.json_path.resolve()
        logger.info(
            "Loading documents from: %s (exists: %s)", resolved_path, resolved_path.exists()
        )

        if not resolved_path.exists():
            logger.warning("JSON file does not exist: %s", resolved_path)
            return []

        try:
            with open(resolved_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and "documents" in data:
                return data["documents"]
            else:
                return []
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Failed to load or parse JSON file: %s - %s", resolved_path, e)
            return []

    def _normalize_text(self, text: str) -> str:
        """Normalize text for fuzzy matching.

        Args:
            text: Input text.

        Returns:
            Normalized text (lowercase, extra spaces removed).
        """
        # Convert to lowercase
        text = text.lower()
        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text)
        # Strip leading/trailing whitespace
        return text.strip()

    def _calculate_relevance_score(self, query: str, document: dict[str, Any]) -> float:
        """Calculate relevance score using fuzzy text matching.

        Scoring strategy:
        - Exact phrase match in title: +0.5
        - Exact phrase match in content: +0.3
        - Partial word matches in title: +0.05 per word
        - Partial word matches in content: +0.02 per word
        - Tag match: +0.1 per tag

        Args:
            query: Search query.
            document: Document dictionary.

        Returns:
            Relevance score (0.0 to 1.0+).
        """
        score = 0.0

        # Normalize query
        query_normalized = self._normalize_text(query)
        query_words = query_normalized.split()

        # Get document fields
        title = self._normalize_text(document.get("title", ""))
        content = self._normalize_text(document.get("content", ""))
        tags = [self._normalize_text(tag) for tag in document.get("tags", [])]

        # Exact phrase match in title
        if query_normalized in title:
            score += 0.5

        # Exact phrase match in content
        if query_normalized in content:
            score += 0.3

        # Partial word matches in title
        for word in query_words:
            if len(word) >= 3 and word in title:
                score += 0.05

        # Partial word matches in content
        for word in query_words:
            if len(word) >= 3 and word in content:
                score += 0.02

        # Tag matches
        for tag in tags:
            if query_normalized in tag or tag in query_normalized:
                score += 0.1
            else:
                # Partial word match in tags
                for word in query_words:
                    if len(word) >= 3 and word in tag:
                        score += 0.05

        # Cap score at 1.0
        return min(score, 1.0)

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun | None = None
    ) -> list[Document]:
        """Retrieve relevant documents.

        Args:
            query: Search query.
            run_manager: Callback manager (optional).

        Returns:
            List of relevant Document objects.
        """
        # Load all documents
        raw_documents = self._load_documents()
        logger.info(
            "LocalJSONRetriever loaded %d documents from %s for query: %s",
            len(raw_documents),
            self.json_path,
            query,
        )

        if not raw_documents:
            logger.warning("No documents loaded, returning empty results")
            return []

        # Score each document
        scored_docs: list[tuple[float, dict[str, Any]]] = []
        for doc in raw_documents:
            score = self._calculate_relevance_score(query, doc)
            if score >= self.min_score:
                scored_docs.append((score, doc))

        logger.info("Found %d documents with score >= %.2f", len(scored_docs), self.min_score)

        # Sort by score (descending)
        scored_docs.sort(key=lambda x: x[0], reverse=True)

        # Take top k
        top_docs = scored_docs[: self.k]

        logger.info("Returning top %d documents (k=%d)", len(top_docs), self.k)

        # Convert to langchain Documents
        results: list[Document] = []
        for score, doc in top_docs:
            metadata = {
                "id": doc.get("id", ""),
                "title": doc.get("title", ""),
                "url": doc.get("url", ""),
                "tags": doc.get("tags", []),
                "category": doc.get("category", ""),
                "relevance_score": score,
            }

            # Remove None values from metadata
            metadata = {k: v for k, v in metadata.items() if v is not None}

            results.append(
                Document(
                    page_content=doc.get("content", ""),
                    metadata=metadata,
                )
            )

        return results
