import asyncio
import re
from html import unescape

import httpx

from app.features.messages.models import MessageRecord
from app.features.run.models import RunRequest, WebSearchRequest
from app.features.web_search.models import WebSearchResult


def extract_web_search(payload: RunRequest) -> WebSearchRequest:
    """Extract web search configuration from a payload."""
    request = payload.web_search or WebSearchRequest()
    engine = payload.web_search_engine or request.engine
    enabled = request.enabled or bool(engine)
    return request.model_copy(update={"enabled": enabled, "engine": engine or None})


def extract_search_query(messages: list[MessageRecord]) -> str:
    """Extract a search query from user messages."""
    for message in reversed(messages):
        if message.role != "user":
            continue
        text_parts = [part.text or "" for part in message.parts if part.type == "text"]
        query = " ".join(part.strip() for part in text_parts if part).strip()
        if query:
            return query
    return ""


def _strip_html_content(raw: str) -> str:
    """Strip HTML content to plain text."""
    text = raw[:200000]
    text = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", text)
    text = re.sub(r"(?is)<[^>]+>", " ", text)
    text = unescape(text)
    return re.sub(r"\\s+", " ", text).strip()


def format_web_search_results(
    engine: str,
    results: list[WebSearchResult],
    content_by_url: dict[str, str] | None = None,
) -> str:
    """Format web search results for inclusion in a prompt."""
    lines = [f"Web search results from {engine}:"]
    for index, result in enumerate(results, start=1):
        lines.append(f"{index}. {result.title}")
        lines.append(f"   URL: {result.url}")
        if result.snippet:
            lines.append(f"   Snippet: {result.snippet}")
        if content_by_url:
            content = content_by_url.get(result.url, "")
            if content:
                lines.append(f"   Content: {content}")
    return "\n".join(lines)


class WebSearchContentFetcher:
    """Fetch and trim web search result content."""

    def __init__(
        self,
        *,
        content_limit: int = 2000,
        concurrency: int = 3,
        timeout: float = 10.0,
    ) -> None:
        self._content_limit = content_limit
        self._concurrency = concurrency
        self._timeout = timeout

    async def fetch(self, results: list[WebSearchResult]) -> dict[str, str]:
        """Fetch and trim content for each result URL."""
        if not results:
            return {}

        semaphore = asyncio.Semaphore(self._concurrency)

        async with httpx.AsyncClient(timeout=self._timeout, follow_redirects=True) as client:

            async def fetch_one(result: WebSearchResult) -> tuple[str, str]:
                url = result.url
                async with semaphore:
                    try:
                        response = await client.get(
                            url,
                            headers={"User-Agent": "Mozilla/5.0"},
                        )
                        response.raise_for_status()
                    except httpx.HTTPError:
                        return (url, "")

                    content_type = response.headers.get("content-type", "")
                    if "text" not in content_type and "html" not in content_type:
                        return (url, "")

                    cleaned = _strip_html_content(response.text)
                    if not cleaned:
                        return (url, "")

                    return (url, cleaned[: self._content_limit])

            tasks = [fetch_one(result) for result in results]
            pairs = await asyncio.gather(*tasks, return_exceptions=False)
            return {url: content for url, content in pairs if content}
