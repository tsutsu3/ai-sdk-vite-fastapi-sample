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
        self._collection = config.vertex_search_collection or "default_collection"
        self._data_store = config.vertex_search_data_store
        self._serving_config = config.vertex_search_serving_config or "default_search"
        self._endpoint = (
            f"{self._location}-discoveryengine.googleapis.com"
            if self._location != "global"
            else None
        )
        logger.info(
            "vertex_search.ready project=%s location=%s data_store=%s",
            self._project_id,
            self._location,
            self._data_store,
        )

    def _build_client(self):
        try:
            from google.cloud import discoveryengine_v1beta as discoveryengine
        except ImportError as exc:
            raise RuntimeError(
                "google-cloud-discoveryengine is required for Vertex AI Search."
            ) from exc
        if self._endpoint:
            return discoveryengine.SearchServiceClient(
                client_options={"api_endpoint": self._endpoint}
            )
        return discoveryengine.SearchServiceClient()

    def _serving_config_path(self) -> str:
        return (
            f"projects/{self._project_id}/locations/{self._location}/collections/{self._collection}"
            f"/dataStores/{self._data_store}/servingConfigs/{self._serving_config}"
        )

    @staticmethod
    def _extract_document_fields(document: Any) -> tuple[str, str | None, str | None]:
        data: dict[str, Any] = {}
        try:
            if document.derived_struct_data:
                data = dict(document.derived_struct_data)
        except Exception:
            data = {}
        if not data:
            try:
                if document.struct_data:
                    data = dict(document.struct_data)
            except Exception:
                data = {}
        title = data.get("title") or data.get("name")
        url = data.get("link") or data.get("url") or data.get("uri")
        text = data.get("snippet") or data.get("text") or data.get("content") or data.get("body")
        return (
            str(text) if isinstance(text, str) else "",
            str(url) if isinstance(url, str) else None,
            str(title) if isinstance(title, str) else None,
        )

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
        client = self._build_client()
        serving_config = self._serving_config_path()
        filter_expression = ""
        if data_source:
            filter_expression = f'data_source = "{data_source}"'

        def _run_search():
            from google.cloud import discoveryengine_v1beta as discoveryengine

            request = discoveryengine.SearchRequest(
                serving_config=serving_config,
                query=query,
                page_size=top_k,
                filter=filter_expression or None,
            )
            return list(client.search(request=request))

        results = await asyncio.to_thread(_run_search)
        output: list[RetrievalResult] = []
        for result in results:
            document = getattr(result, "document", None)
            if not document:
                continue
            text, url, title = self._extract_document_fields(document)
            if not url:
                continue
            output.append(
                RetrievalResult(
                    text=text or "",
                    url=url,
                    title=title,
                    score=getattr(result, "score", None),
                )
            )
            if len(output) >= top_k:
                break
        return output
