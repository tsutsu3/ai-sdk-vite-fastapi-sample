from __future__ import annotations

import asyncio
import random
from collections.abc import Iterable, Sequence
from pathlib import Path

from app.features.retrieval.providers.base import RetrievalProvider
from app.features.retrieval.schemas import RetrievalResult


class LocalFileRetrievalProvider(RetrievalProvider):
    id = "local-files"
    name = "Local Files"

    @staticmethod
    def _resolve_base_path(base_path: str) -> Path:
        candidate = Path(base_path)
        if candidate.exists():
            return candidate
        if not candidate.is_absolute():
            repo_root = Path(__file__).resolve().parents[5]
            fallback = (repo_root / base_path).resolve()
            if fallback.exists():
                return fallback
        return candidate

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
        self._base_path = self._resolve_base_path(base_path)
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
        return self._snippet_from_match(content, index, match_len)

    def _snippet_from_match(self, content: str, index: int, match_len: int) -> str:
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

    def _find_matches(self, lowered: str, needle: str) -> list[tuple[int, int]]:
        if not needle:
            return []
        matches: list[tuple[int, int]] = []
        start = 0
        while True:
            index = lowered.find(needle, start)
            if index < 0:
                break
            matches.append((index, len(needle)))
            start = index + len(needle)
        tokens = [token for token in needle.split() if len(token) >= 3]
        for token in sorted(tokens, key=len, reverse=True):
            start = 0
            while True:
                index = lowered.find(token, start)
                if index < 0:
                    break
                matches.append((index, len(token)))
                start = index + len(token)
        seen: set[int] = set()
        unique: list[tuple[int, int]] = []
        for index, match_len in matches:
            if index in seen:
                continue
            seen.add(index)
            unique.append((index, match_len))
        unique.sort(key=lambda item: item[0])
        return unique

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

        await asyncio.sleep(random.random())

        results: list[RetrievalResult] = []
        for path in self._iter_files(data_source):
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if self._max_bytes and len(text.encode("utf-8")) > self._max_bytes:
                text = text.encode("utf-8")[: self._max_bytes].decode("utf-8", errors="ignore")
            lowered = text.lower()
            needle = query.lower().strip()
            matches = self._find_matches(lowered, needle)
            if not matches:
                continue
            relative = str(path.relative_to(self._base_path))
            remaining = max(top_k - len(results), 0)
            for index, match_len in matches[:remaining]:
                snippet = self._snippet_from_match(text, index, match_len)
                if not snippet:
                    continue
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
            if len(results) >= top_k:
                break
        return results
