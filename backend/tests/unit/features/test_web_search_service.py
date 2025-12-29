import pytest

from app.features.web_search.models import WebSearchResult
from app.features.web_search.providers.base import WebSearchProvider
from app.features.web_search.service import WebSearchService


class StubProvider(WebSearchProvider):
    id = "stub"
    name = "Stub"

    async def search(self, query: str, count: int = 5):
        return [WebSearchResult(title="t", url="u", snippet="s")][:count]


@pytest.mark.asyncio
async def test_default_engine_fallback():
    service = WebSearchService({"stub": StubProvider()})
    results = await service.search("hello")
    assert len(results) == 1


@pytest.mark.asyncio
async def test_resolve_unknown_engine_returns_default():
    service = WebSearchService({"stub": StubProvider()}, default_engine="stub")
    results = await service.search("hello", engine="missing")
    assert len(results) == 1
