from __future__ import annotations

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError

from alembic import command
from app.core.config import Settings
from app.db.session import create_session_factory
from app.seed import seed_demo_content
from tests.postgres_support import alembic_config, postgres_url, requires_postgres

pytestmark = requires_postgres
__all__ = ["postgres_url"]

INSERT_PROFILE = text(
    "INSERT INTO profiles (full_name, headline, summary, location, target_roles,"
    " email, published) VALUES (:name, 'Headline', 'Summary', 'Los Angeles', '',"
    " '', :published)"
)
RESUME_TABLES = {
    "profiles",
    "skills",
    "experiences",
    "experience_accomplishments",
    "experience_skills",
    "projects",
    "project_skills",
    "education",
}


def _engine(url: str):
    return create_engine(Settings(database_url=url).database_url)


def test_upgrade_head_builds_the_schema(postgres_url: str) -> None:
    command.upgrade(alembic_config(), "head")

    engine = _engine(postgres_url)
    with engine.connect() as connection:
        version = connection.execute(
            text("SELECT version_num FROM alembic_version")
        ).scalar_one()
    tables = set(inspect(engine).get_table_names())
    engine.dispose()

    assert version == "20261006_04"
    assert RESUME_TABLES <= tables


def test_many_profiles_can_be_unpublished_but_only_one_published(
    postgres_url: str,
) -> None:
    command.upgrade(alembic_config(), "head")
    engine = _engine(postgres_url)

    with engine.begin() as connection:
        connection.execute(INSERT_PROFILE, {"name": "Draft One", "published": False})
        connection.execute(INSERT_PROFILE, {"name": "Draft Two", "published": False})
        connection.execute(INSERT_PROFILE, {"name": "Live One", "published": True})

    with pytest.raises(IntegrityError), engine.begin() as connection:
        connection.execute(INSERT_PROFILE, {"name": "Live Two", "published": True})
    engine.dispose()


def test_seed_runs_against_postgres(postgres_url: str, sample_seed) -> None:
    command.upgrade(alembic_config(), "head")
    engine, session_factory = create_session_factory(Settings().database_url)

    seed_demo_content(session_factory=session_factory)
    seed_demo_content(session_factory=session_factory)

    with engine.connect() as connection:
        published = connection.execute(
            text("SELECT count(*) FROM profiles WHERE published")
        ).scalar_one()
    engine.dispose()
    assert published == 1
