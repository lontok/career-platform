from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text

from alembic import command
from app.copy_sqlite import copy_database, main, open_sqlite_read_only
from app.core.config import Settings
from app.db.session import create_session_factory
from app.seed import seed_demo_content
from tests.postgres_support import alembic_config, postgres_url, requires_postgres

__all__ = ["postgres_url"]

COPIED_TABLES = (
    "profiles",
    "skills",
    "experiences",
    "experience_accomplishments",
    "experience_skills",
    "projects",
    "project_skills",
    "education",
)


def _build_source(monkeypatch, folder: Path, revision: str = "head") -> Path:
    # The space in the folder name matches this repo's "My Drive" path.
    folder.mkdir()
    database = folder / "resume.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database}")
    command.upgrade(alembic_config(), revision)
    return database


def _seed_source(database: Path) -> None:
    engine, session_factory = create_session_factory(f"sqlite:///{database}")
    seed_demo_content(session_factory=session_factory)
    engine.dispose()


def _counts(engine) -> dict[str, int]:
    with engine.connect() as connection:
        return {
            table: connection.execute(
                text(f"SELECT count(*) FROM {table}")
            ).scalar_one()
            for table in COPIED_TABLES
        }


def test_main_refuses_a_missing_file(tmp_path: Path) -> None:
    with pytest.raises(SystemExit, match="No SQLite file"):
        main([str(tmp_path / "missing.db")])


def test_main_refuses_a_sqlite_target(monkeypatch, tmp_path: Path) -> None:
    source = tmp_path / "resume.db"
    sqlite3.connect(source).close()
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'target.db'}")

    with pytest.raises(SystemExit, match="must point at Postgres"):
        main([str(source)])


@requires_postgres
def test_copy_matches_every_table_and_resets_sequences(
    monkeypatch, tmp_path: Path, postgres_url: str, sample_seed
) -> None:
    source_path = _build_source(monkeypatch, tmp_path / "My Drive")
    _seed_source(source_path)
    monkeypatch.setenv("DATABASE_URL", postgres_url)
    command.upgrade(alembic_config(), "head")

    source = open_sqlite_read_only(source_path)
    target = create_engine(Settings().database_url)
    copied = copy_database(source, target)
    source_counts = _counts(source)
    target_counts = _counts(target)

    with target.begin() as connection:
        largest = connection.execute(text("SELECT max(id) FROM skills")).scalar_one()
        new_id = connection.execute(
            text(
                "INSERT INTO skills (name, category, published, display_order)"
                " VALUES ('Added Later', 'misc', false, 99) RETURNING id"
            )
        ).scalar_one()
    source.dispose()
    target.dispose()

    assert copied == source_counts
    assert target_counts == source_counts
    assert source_counts["experience_accomplishments"] > 0
    assert new_id > largest


@requires_postgres
def test_copy_refuses_a_target_that_has_rows(
    monkeypatch, tmp_path: Path, postgres_url: str, sample_seed
) -> None:
    source_path = _build_source(monkeypatch, tmp_path / "source db")
    _seed_source(source_path)
    monkeypatch.setenv("DATABASE_URL", postgres_url)
    command.upgrade(alembic_config(), "head")
    source = open_sqlite_read_only(source_path)
    target = create_engine(Settings().database_url)
    copy_database(source, target)

    with pytest.raises(ValueError, match="is not empty"):
        copy_database(source, target)
    source_counts = _counts(source)
    target_counts = _counts(target)
    source.dispose()
    target.dispose()

    assert target_counts == source_counts


@requires_postgres
def test_copy_refuses_mismatched_revisions(
    monkeypatch, tmp_path: Path, postgres_url: str
) -> None:
    source_path = _build_source(
        monkeypatch, tmp_path / "old db", revision="20261006_03"
    )
    monkeypatch.setenv("DATABASE_URL", postgres_url)
    command.upgrade(alembic_config(), "head")
    source = open_sqlite_read_only(source_path)
    target = create_engine(Settings().database_url)

    with pytest.raises(ValueError, match="20261006_03"):
        copy_database(source, target)
    source.dispose()
    target.dispose()
