import json
import os

from sqlalchemy import Column, MetaData, String, Table, Text, create_engine, delete, insert, select
from sqlalchemy.engine import Engine

from app.store import StoreEntry

metadata = MetaData()

store_entries = Table(
    "store_entries",
    metadata,
    Column("id", String, nullable=False),
    Column("kind", String, nullable=False),
    Column("handle", String, nullable=False),
    Column("text", Text, nullable=False),
    Column("embedding", Text, nullable=False),
)


def engine_from_env() -> Engine:
    """Builds the Neon/Postgres engine from DATABASE_URL."""
    return create_engine(os.environ["DATABASE_URL"])


def _ensure_schema(engine: Engine) -> None:
    metadata.create_all(engine)


def save_entries(engine: Engine, entries: list[StoreEntry]) -> None:
    _ensure_schema(engine)

    with engine.begin() as conn:
        conn.execute(delete(store_entries))
        if entries:
            conn.execute(
                insert(store_entries),
                [
                    {
                        "id": entry.id,
                        "kind": entry.kind,
                        "handle": entry.handle,
                        "text": entry.text,
                        "embedding": json.dumps(entry.embedding),
                    }
                    for entry in entries
                ],
            )


def load_entries(engine: Engine) -> list[StoreEntry]:
    _ensure_schema(engine)

    with engine.connect() as conn:
        rows = conn.execute(select(store_entries)).all()

    return [
        StoreEntry(
            id=row.id,
            kind=row.kind,
            handle=row.handle,
            text=row.text,
            embedding=json.loads(row.embedding),
        )
        for row in rows
    ]
