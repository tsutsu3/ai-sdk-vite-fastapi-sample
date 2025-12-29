from collections.abc import Sequence

from app.features.retrieval.providers.base import RetrievalProvider
from app.features.retrieval.schemas import RetrievalResult


class PostgresRetrievalProvider(RetrievalProvider):
    id = "postgres"
    name = "Postgres (pgvector)"

    def __init__(
        self,
        dsn: str,
        table: str,
        text_column: str,
        url_column: str,
        embedding_column: str,
        source_column: str,
    ) -> None:
        self._dsn = dsn
        self._table = table
        self._text_column = text_column
        self._url_column = url_column
        self._embedding_column = embedding_column
        self._source_column = source_column

    async def search(
        self,
        query: str,
        data_source: str,
        top_k: int = 5,
        *,
        query_embedding: list[float] | None = None,
    ) -> Sequence[RetrievalResult]:
        if not (self._dsn and self._table):
            return []
        if not query_embedding:
            raise ValueError("queryEmbedding is required for postgres provider.")

        try:
            import asyncpg
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("asyncpg is required for postgres rag provider.") from exc

        vector = "[" + ",".join(str(x) for x in query_embedding) + "]"
        sql = (
            f"SELECT {self._text_column} AS text, "
            f"{self._url_column} AS url, "
            f"1 - ({self._embedding_column} <=> $1::vector) AS score "
            f"FROM {self._table} "
            f"WHERE {self._source_column} = $2 "
            f"ORDER BY {self._embedding_column} <=> $1::vector "
            f"LIMIT $3"
        )
        conn = await asyncpg.connect(self._dsn)
        try:
            rows = await conn.fetch(sql, vector, data_source, top_k)
        finally:
            await conn.close()

        results: list[RetrievalResult] = []
        for row in rows:
            text = row.get("text")
            url = row.get("url")
            score = row.get("score")
            if isinstance(text, str) and isinstance(url, str):
                results.append(
                    RetrievalResult(
                        text=text.strip(),
                        url=url.strip(),
                        score=float(score) if isinstance(score, (int, float)) else None,
                    )
                )
        return results
