import asyncio
from logging import getLogger
from typing import Any

from app.core.config import AppConfig
from app.features.retrieval.providers.base import RetrievalProvider
from app.features.retrieval.schemas import RetrievalResult

logger = getLogger(__name__)


class VertexSearchProvider(RetrievalProvider):
    id = "vertex-search"
    name = "Vertex AI Search"

    def __init__(self, config: AppConfig) -> None:
        if not (
            config.vertex_search_project_id
            and config.vertex_search_location
            and config.vertex_search_data_store
        ):
            raise RuntimeError("Vertex AI Search settings are not configured.")
        self._project_id = config.vertex_search_project_id
        self._location = config.vertex_search_location
        self._data_store = config.vertex_search_data_store
        self._serving_config = config.vertex_search_serving_config or "default_search"
        self._engine_data_type = 0
        logger.info(
            "vertex_search.ready project=%s location=%s data_store=%s",
            self._project_id,
            self._location,
            self._data_store,
        )

    @staticmethod
    def _extract_document_fields(metadata: dict[str, Any], text: str) -> tuple[str, str | None, str | None]:
        title = metadata.get("title") or metadata.get("name")
        url = metadata.get("source") or metadata.get("link") or metadata.get("url")
        return (
            text,
            str(url) if isinstance(url, str) and url else None,
            str(title) if isinstance(title, str) and title else None,
        )

    def _build_retriever(self, *, data_source: str, top_k: int):
        try:
            from langchain_google_community.vertex_ai_search import (
                VertexAISearchRetriever,
                VertexAISearchSummaryTool,
            )
        except ImportError as exc:
            raise RuntimeError(
                "langchain-google-community is required for Vertex AI Search."
            ) from exc
        filter_expression = ""
        if data_source:
            filter_expression = f'data_source = "{data_source}"'
        retriever = VertexAISearchRetriever(
            project_id=self._project_id,
            location_id=self._location,
            data_store_id=self._data_store,
            serving_config_id=self._serving_config,
            engine_data_type=self._engine_data_type,
            max_documents=top_k,
            filter=filter_expression or None,
            custom_embedding_ratio=None,
        )
        summary_tool = VertexAISearchSummaryTool(
            name="vertex-ai-search-summary",
            description="Summarize Vertex AI Search results with citations.",
            project_id=self._project_id,
            location_id=self._location,
            data_store_id=self._data_store,
            serving_config_id=self._serving_config,
            engine_data_type=self._engine_data_type,
            max_documents=top_k,
            filter=filter_expression or None,
            custom_embedding_ratio=None,
        )
        return retriever, summary_tool

    async def search(
        self,
        query: str,
        data_source: str,
        top_k: int = 5,
        *,
        query_embedding: list[float] | None = None,
    ) -> list[RetrievalResult]:
        if not query:
            return []
        retriever, _ = self._build_retriever(data_source=data_source, top_k=top_k)
        documents = await asyncio.to_thread(retriever.invoke, query)
        output: list[RetrievalResult] = []
        for doc in documents:
            metadata = dict(getattr(doc, "metadata", {}) or {})
            text = getattr(doc, "page_content", "") or ""
            text, url, title = self._extract_document_fields(metadata, text)
            if not url:
                continue
            output.append(RetrievalResult(text=text or "", url=url, title=title))
            if len(output) >= top_k:
                break
        return output

    async def search_with_answer(
        self,
        query: str,
        data_source: str,
        top_k: int = 5,
        *,
        summary_prompt: str | None = None,
    ) -> tuple[list[RetrievalResult], str]:
        if not query:
            return [], ""
        retriever, summary_tool = self._build_retriever(
            data_source=data_source, top_k=top_k
        )
        summary_tool.summary_result_count = min(top_k, 5)
        summary_tool.summary_include_citations = True
        if summary_prompt:
            summary_tool.summary_prompt = summary_prompt
        summary_text = await asyncio.to_thread(summary_tool.run, query)
        documents = await asyncio.to_thread(retriever.invoke, query)
        output: list[RetrievalResult] = []
        for doc in documents:
            metadata = dict(getattr(doc, "metadata", {}) or {})
            text = getattr(doc, "page_content", "") or ""
            text, url, title = self._extract_document_fields(metadata, text)
            if not url:
                continue
            output.append(RetrievalResult(text=text or "", url=url, title=title))
            if len(output) >= top_k:
                break
        return output, summary_text.strip()
