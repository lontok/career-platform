from __future__ import annotations

import sqlite3
from pathlib import Path

from alembic.config import Config

from alembic import command

REPO_ROOT = Path(__file__).resolve().parent.parent


def _alembic_config() -> Config:
    config = Config(str(REPO_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(REPO_ROOT / "alembic"))
    return config


def test_upgrade_keeps_experience_children(monkeypatch, tmp_path) -> None:
    database = tmp_path / "upgrade.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database}")
    config = _alembic_config()
    command.upgrade(config, "20260917_02")

    with sqlite3.connect(database) as connection:
        connection.execute(
            "INSERT INTO experiences (id, role_title, organization, location,"
            " start_date, is_current, summary, published, display_order)"
            " VALUES (1, 'Analyst', 'Acme', 'Los Angeles', '2024-01-01', 1,"
            " 'Built reports.', 1, 1)"
        )
        connection.execute(
            "INSERT INTO skills (id, name, category, published, display_order)"
            " VALUES (1, 'SQL', 'analytics', 1, 1)"
        )
        connection.execute(
            "INSERT INTO experience_accomplishments"
            " (id, experience_id, statement, display_order)"
            " VALUES (1, 1, 'Cut report time in half.', 1)"
        )
        connection.execute(
            "INSERT INTO experience_skills (experience_id, skill_id) VALUES (1, 1)"
        )

    command.upgrade(config, "head")

    with sqlite3.connect(database) as connection:
        accomplishments = connection.execute(
            "SELECT statement FROM experience_accomplishments"
        ).fetchall()
        links = connection.execute(
            "SELECT experience_id, skill_id FROM experience_skills"
        ).fetchall()
        featured = connection.execute(
            "SELECT featured FROM experiences WHERE id = 1"
        ).fetchone()

    assert accomplishments == [("Cut report time in half.",)]
    assert links == [(1, 1)]
    assert featured == (0,)

    command.downgrade(config, "20260917_02")

    with sqlite3.connect(database) as connection:
        columns = [
            row[1] for row in connection.execute("PRAGMA table_info(experiences)")
        ]
        accomplishments_after_downgrade = connection.execute(
            "SELECT COUNT(*) FROM experience_accomplishments"
        ).fetchone()
        links_after_downgrade = connection.execute(
            "SELECT COUNT(*) FROM experience_skills"
        ).fetchone()

    assert "featured" not in columns
    assert accomplishments_after_downgrade == (1,)
    assert links_after_downgrade == (1,)
