"""Copy every resume row from a SQLite file into an empty, migrated Postgres.

Usage: DATABASE_URL=<postgres url> uv run python -m app.copy_sqlite <sqlite file>
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

from sqlalchemy import Engine, create_engine, func, select, text

from app import models  # noqa: F401
from app.core.config import Settings
from app.db.base import Base


def open_sqlite_read_only(path: Path) -> Engine:
    # as_uri() percent-encodes spaces, which a hand-built sqlite URL would not.
    uri = f"{Path(path).resolve().as_uri()}?mode=ro"
    return create_engine("sqlite://", creator=lambda: sqlite3.connect(uri, uri=True))


def copy_database(source: Engine, target: Engine) -> dict[str, int]:
    source_version = _alembic_version(source)
    target_version = _alembic_version(target)
    if source_version != target_version:
        raise ValueError(
            f"Source is at {source_version} but target is at {target_version}"
        )

    tables = Base.metadata.sorted_tables
    copied: dict[str, int] = {}
    with source.connect() as reader, target.begin() as writer:
        for table in tables:
            if writer.scalar(select(func.count()).select_from(table)):
                raise ValueError(f"Target table {table.name} is not empty")

        for table in tables:
            rows = [dict(row._mapping) for row in reader.execute(select(table))]
            if rows:
                writer.execute(table.insert(), rows)
            copied[table.name] = len(rows)

        # Rows arrive with their SQLite IDs, so move each sequence past them.
        for table in tables:
            if "id" in table.c and table.c.id.primary_key:
                writer.execute(
                    text(
                        f"SELECT setval(pg_get_serial_sequence('{table.name}', 'id'),"
                        f" COALESCE((SELECT max(id) FROM {table.name}), 1),"
                        f" (SELECT max(id) FROM {table.name}) IS NOT NULL)"
                    )
                )
    return copied


def main(argv: list[str] | None = None) -> None:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        raise SystemExit("Usage: python -m app.copy_sqlite <sqlite file>")

    source_path = Path(args[0])
    if not source_path.is_file():
        raise SystemExit(f"No SQLite file at {source_path}")

    target_url = Settings().database_url
    if not target_url.startswith("postgresql+psycopg://"):
        raise SystemExit("DATABASE_URL must point at Postgres")

    source = open_sqlite_read_only(source_path)
    target = create_engine(target_url)
    try:
        copied = copy_database(source, target)
    finally:
        source.dispose()
        target.dispose()

    for table_name, count in copied.items():
        print(f"{table_name}: {count}")


def _alembic_version(engine: Engine) -> str:
    with engine.connect() as connection:
        return connection.execute(
            text("SELECT version_num FROM alembic_version")
        ).scalar_one()


if __name__ == "__main__":
    main()
