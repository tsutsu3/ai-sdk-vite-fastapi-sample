import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.core.config import Settings  # noqa: E402


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ingest documents with embeddings into a pgvector table.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--input", required=True, help="Path to JSON or JSONL (use - for stdin).")
    parser.add_argument(
        "--format",
        choices=("json", "jsonl"),
        default="jsonl",
        help="Input format (default: jsonl).",
    )
    parser.add_argument("--dsn", default=None, help="Postgres DSN (overrides env).")
    parser.add_argument("--table", default=None, help="Table name (overrides env).")
    parser.add_argument("--text-column", default=None, help="Text column name.")
    parser.add_argument("--url-column", default=None, help="URL column name.")
    parser.add_argument("--embedding-column", default=None, help="Embedding column name.")
    parser.add_argument("--source-column", default=None, help="Data source column name.")
    parser.add_argument(
        "--data-source",
        default=None,
        help="Default data_source value when missing in input records.",
    )
    parser.add_argument(
        "--create-table",
        action="store_true",
        help="Create pgvector extension and table if missing.",
    )
    parser.add_argument(
        "--create-index",
        action="store_true",
        help="Create an ivfflat index on the embedding column.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Batch size for inserts (default: 100).",
    )
    return parser.parse_args()


def _read_input(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    return Path(path).read_text(encoding="utf-8")


def _iter_records(raw: str, fmt: str) -> Iterable[dict[str, Any]]:
    if fmt == "json":
        data = json.loads(raw)
        if not isinstance(data, list):
            raise ValueError("JSON input must be a list of objects.")
        for item in data:
            if not isinstance(item, dict):
                raise ValueError("Each JSON item must be an object.")
            yield item
        return

    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        item = json.loads(line)
        if not isinstance(item, dict):
            raise ValueError("Each JSONL line must be an object.")
        yield item


def _normalize_record(
    item: dict[str, Any],
    *,
    default_source: str | None,
) -> dict[str, Any]:
    content = item.get("content", item.get("text"))
    url = item.get("source_url", item.get("url"))
    embedding = item.get("embedding")
    data_source = item.get("data_source", default_source)

    if not isinstance(content, str) or not content.strip():
        raise ValueError("Record content/text must be a non-empty string.")
    if not isinstance(url, str) or not url.strip():
        raise ValueError("Record source_url/url must be a non-empty string.")
    if not isinstance(embedding, list) or not embedding:
        raise ValueError("Record embedding must be a non-empty list.")
    if not all(isinstance(value, (int, float)) for value in embedding):
        raise ValueError("Record embedding must contain numbers only.")
    if not isinstance(data_source, str) or not data_source.strip():
        raise ValueError("Record data_source is required.")

    return {
        "content": content.strip(),
        "url": url.strip(),
        "embedding": [float(value) for value in embedding],
        "data_source": data_source.strip(),
    }


def _validate_identifier(name: str) -> list[str]:
    parts = name.split(".")
    for part in parts:
        if not part or not part.replace("_", "").isalnum():
            raise ValueError(f"Invalid identifier: {name}")
    return parts


def _quote_identifier(name: str) -> str:
    parts = _validate_identifier(name)
    return ".".join(f'"{part}"' for part in parts)


async def _ensure_schema(
    conn,
    *,
    table: str,
    text_column: str,
    url_column: str,
    embedding_column: str,
    source_column: str,
    embedding_dim: int,
    create_index: bool,
) -> None:
    table_sql = _quote_identifier(table)
    text_sql = _quote_identifier(text_column)
    url_sql = _quote_identifier(url_column)
    embedding_sql = _quote_identifier(embedding_column)
    source_sql = _quote_identifier(source_column)

    await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
    await conn.execute(
        f"CREATE TABLE IF NOT EXISTS {table_sql} ("
        "id BIGSERIAL PRIMARY KEY, "
        f"{text_sql} TEXT NOT NULL, "
        f"{url_sql} TEXT NOT NULL, "
        f"{embedding_sql} VECTOR({embedding_dim}) NOT NULL, "
        f"{source_sql} TEXT NOT NULL"
        ")"
    )

    if create_index:
        index_name = f"{table.replace('.', '_')}_{embedding_column}_ivfflat_idx"
        index_sql = _quote_identifier(index_name)
        await conn.execute(
            f"CREATE INDEX IF NOT EXISTS {index_sql} "
            f"ON {table_sql} USING ivfflat ({embedding_sql} vector_cosine_ops) "
            "WITH (lists = 100)"
        )


async def _ingest() -> None:
    args = _parse_args()
    settings = Settings()
    dsn = args.dsn or settings.retrieval_pg_dsn
    if not dsn:
        raise RuntimeError("Postgres DSN is required (RETRIEVAL_PG_DSN or --dsn).")

    table = args.table or settings.retrieval_pg_table
    text_column = args.text_column or settings.retrieval_pg_text_column
    url_column = args.url_column or settings.retrieval_pg_url_column
    embedding_column = args.embedding_column or settings.retrieval_pg_embedding_column
    source_column = args.source_column or settings.retrieval_pg_source_column

    raw = _read_input(args.input)
    records: list[dict[str, Any]] = []
    embedding_dim: int | None = None
    for item in _iter_records(raw, args.format):
        record = _normalize_record(item, default_source=args.data_source)
        if embedding_dim is None:
            embedding_dim = len(record["embedding"])
        elif embedding_dim != len(record["embedding"]):
            raise ValueError("All embeddings must have the same dimension.")
        records.append(record)

    if not records:
        raise RuntimeError("No records found in input.")

    try:
        import asyncpg
    except ImportError as exc:
        raise RuntimeError("asyncpg is required to ingest pgvector data.") from exc

    conn = await asyncpg.connect(dsn)
    try:
        if args.create_table:
            await _ensure_schema(
                conn,
                table=table,
                text_column=text_column,
                url_column=url_column,
                embedding_column=embedding_column,
                source_column=source_column,
                embedding_dim=embedding_dim or 0,
                create_index=args.create_index,
            )

        table_sql = _quote_identifier(table)
        text_sql = _quote_identifier(text_column)
        url_sql = _quote_identifier(url_column)
        embedding_sql = _quote_identifier(embedding_column)
        source_sql = _quote_identifier(source_column)
        insert_sql = (
            f"INSERT INTO {table_sql} "
            f"({text_sql}, {url_sql}, {embedding_sql}, {source_sql}) "
            "VALUES ($1, $2, $3::vector, $4)"
        )

        batch: list[tuple[str, str, str, str]] = []
        for record in records:
            vector = "[" + ",".join(str(value) for value in record["embedding"]) + "]"
            batch.append(
                (
                    record["content"],
                    record["url"],
                    vector,
                    record["data_source"],
                )
            )
            if len(batch) >= args.batch_size:
                await conn.executemany(insert_sql, batch)
                batch.clear()
        if batch:
            await conn.executemany(insert_sql, batch)
    finally:
        await conn.close()


def main() -> None:
    asyncio.run(_ingest())


if __name__ == "__main__":
    main()
