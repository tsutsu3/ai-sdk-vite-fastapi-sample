from __future__ import annotations

from collections.abc import Iterable, Sequence
from pathlib import Path

from app.features.retrieval.providers.base import RetrievalProvider
from app.features.retrieval.schemas import RetrievalResult


class LocalFileRetrievalProvider(RetrievalProvider):
    id = "local-files"
    name = "Local Files"

    def __init__(
        self,
        base_path: str,
        *,
        allowed_extensions: Iterable[str] = (
            ".txt",
            ".md",
            ".csv",
            ".json",
            ".html",
            ".log",
        ),
        max_files: int = 200,
        max_bytes: int = 200_000,
        snippet_chars: int = 400,
    ) -> None:
        self._base_path = Path(base_path)
        self._allowed_extensions = {ext.lower() for ext in allowed_extensions}
        self._max_files = max_files
        self._max_bytes = max_bytes
        self._snippet_chars = snippet_chars

    def _iter_files(self, data_source: str) -> Iterable[Path]:
        base = self._base_path.resolve()
        target = (base / data_source).resolve() if data_source else base
        if not target.exists() or not target.is_dir():
            return []
        if base not in target.parents and base != target:
            return []

        count = 0
        for path in target.rglob("*"):
            if count >= self._max_files:
                break
            if not path.is_file():
                continue
            if path.suffix.lower() not in self._allowed_extensions:
                continue
            count += 1
            yield path

    def _match_snippet(self, content: str, query: str) -> str:
        lowered = content.lower()
        needle = query.lower().strip()
        match = self._find_match(lowered, needle)
        if match is None:
            return ""
        index, match_len = match
        half = max(20, self._snippet_chars // 2)
        start = max(0, index - half)
        end = min(len(content), index + match_len + half)
        snippet = content[start:end].replace("\n", " ").strip()
        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."
        return snippet

    def _find_match(self, lowered: str, needle: str) -> tuple[int, int] | None:
        if not needle:
            return None
        index = lowered.find(needle)
        if index >= 0:
            return index, len(needle)
        tokens = [token for token in needle.split() if len(token) >= 3]
        for token in sorted(tokens, key=len, reverse=True):
            index = lowered.find(token)
            if index >= 0:
                return index, len(token)
        return None

    async def search(
        self,
        query: str,
        data_source: str,
        top_k: int = 5,
        *,
        query_embedding: list[float] | None = None,
    ) -> Sequence[RetrievalResult]:
        if not query or not self._base_path.exists():
            return []

        results: list[RetrievalResult] = []
        for path in self._iter_files(data_source):
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if self._max_bytes and len(text.encode("utf-8")) > self._max_bytes:
                text = text.encode("utf-8")[: self._max_bytes].decode("utf-8", errors="ignore")
            snippet = self._match_snippet(text, query)
            if not snippet:
                continue
            relative = str(path.relative_to(self._base_path))
            results.append(
                RetrievalResult(
                    text=snippet,
                    url=relative,
                    title=path.name,
                    score=1.0,
                )
            )
            if len(results) >= top_k:
                break
        return results
