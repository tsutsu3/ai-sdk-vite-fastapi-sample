import asyncio
from collections.abc import Sequence
import re
from typing import Any

from ddgs import DDGS

from app.features.web_search.models import WebSearchResult
from app.features.web_search.providers.base import WebSearchProvider


class DuckDuckGoSearchProvider(WebSearchProvider):
    id = "duckduckgo"
    name = "DuckDuckGo"

    @staticmethod
    def _is_allowed(result: dict) -> bool:
        url = result.get("href", "")
        title = result.get("title", "")
        body = result.get("body", "")

        blocked_domains = (
            ".cn/",
            "zhihu.com",
            "baidu.com",
        )

        if any(d in url for d in blocked_domains):
            return False

        if re.search(r"[\u4e00-\u9fff]", title + body):
            return False

        return True

    async def search(self, query: str, count: int = 5) -> Sequence[WebSearchResult]:
        def run_search() -> list[dict[str, Any]]:
            with DDGS() as ddgs:
                return list(
                    ddgs.text(
                        query
                        + " -lang:zh -site:cn -site:baidu.com -site:zhihu.com -site:zhuanlan.zhihu.com",
                        max_results=count * 2,  # Fetch extra to account for filtering
                        region="us-en",
                    )
                )

        items = await asyncio.to_thread(run_search)

        results: list[WebSearchResult] = []

        for item in items:
            if not self._is_allowed(item):
                continue

            title = item.get("title")
            url = item.get("href")
            snippet = item.get("body")

            if not isinstance(title, str) or not isinstance(url, str):
                continue

            results.append(
                WebSearchResult(
                    title=title.strip(),
                    url=url.strip(),
                    snippet=snippet.strip() if isinstance(snippet, str) else None,
                )
            )

            if len(results) >= count:
                break

        return results
