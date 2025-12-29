from collections.abc import Sequence
from typing import Any

import httpx

from app.features.retrieval.providers.base import RetrievalProvider
from app.features.retrieval.schemas import RetrievalResult


class AISearchProvider(RetrievalProvider):
    id = "ai-search"
    name = "AI Search"

    def __init__(
        self, url: str, api_key: str | None = None, auth_header: str = "X-API-Key"
    ) -> None:
        self._url = url
        self._api_key = api_key
        self._auth_header = auth_header

    async def search(
        self,
        query: str,
        data_source: str,
        top_k: int = 5,
        *,
        query_embedding: list[float] | None = None,
    ) -> Sequence[RetrievalResult]:
        if not self._url:
            return []
        headers: dict[str, str] = {}
        if self._api_key:
            headers[self._auth_header] = self._api_key
        payload: dict[str, Any] = {
            "query": query,
            "topK": top_k,
            "dataSource": data_source,
        }
        if query_embedding:
            payload["queryEmbedding"] = query_embedding
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(self._url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        items = data.get("results") or data.get("items") or []
        results: list[RetrievalResult] = []
        if isinstance(items, list):
            for item in items:
                if len(results) >= top_k:
                    break
                if not isinstance(item, dict):
                    continue
                text = item.get("text") or item.get("content") or item.get("chunk")
                url = item.get("url") or item.get("sourceUrl") or item.get("source_url")
                title = item.get("title") or item.get("name")
                score = item.get("score")
                if isinstance(text, str) and isinstance(url, str):
                    results.append(
                        RetrievalResult(
                            text=text.strip(),
                            url=url.strip(),
                            title=title.strip() if isinstance(title, str) else None,
                            score=float(score) if isinstance(score, (int, float)) else None,
                        )
                    )
        return results
