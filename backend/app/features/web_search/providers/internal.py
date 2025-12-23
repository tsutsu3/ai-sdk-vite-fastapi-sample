from collections.abc import Sequence
from typing import Any

import httpx

from app.features.web_search.models import WebSearchResult
from app.features.web_search.providers.base import WebSearchProvider


class InternalSearchProvider(WebSearchProvider):
    id = "internal"
    name = "Internal Search"

    def __init__(self, url: str, api_key: str | None = None, auth_header: str = "X-API-Key") -> None:
        self._url = url
        self._api_key = api_key
        self._auth_header = auth_header

    async def search(self, query: str, count: int = 5) -> Sequence[WebSearchResult]:
        headers = {}
        if self._api_key:
            headers[self._auth_header] = self._api_key
        payload = {"query": query, "count": count}
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(self._url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        items = data.get("results") or data.get("items") or []
        results: list[WebSearchResult] = []
        if isinstance(items, list):
            for item in items:
                if len(results) >= count:
                    break
                if not isinstance(item, dict):
                    continue
                title = item.get("title") or item.get("name")
                url = item.get("url") or item.get("link")
                snippet = item.get("snippet") or item.get("summary")
                if isinstance(title, str) and isinstance(url, str):
                    results.append(
                        WebSearchResult(
                            title=title.strip(),
                            url=url.strip(),
                            snippet=snippet.strip() if isinstance(snippet, str) else None,
                        )
                    )
        return results
