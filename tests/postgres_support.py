from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import urlsplit

import pytest
from alembic.config import Config
from sqlalchemy import create_engine, text

from app.core.config import Settings

REPO_ROOT = Path(__file__).resolve().parent.parent
POSTGRES_URL = os.environ.get("TEST_POSTGRES_URL")
LOCAL_HOSTS = {"localhost", "127.0.0.1"}

requires_postgres = pytest.mark.skipif(
    not POSTGRES_URL, reason="TEST_POSTGRES_URL is not set"
)


def alembic_config() -> Config:
    config = Config(str(REPO_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(REPO_ROOT / "alembic"))
    return config


@pytest.fixture
def postgres_url(monkeypatch) -> str:
    if urlsplit(POSTGRES_URL).hostname not in LOCAL_HOSTS:
        pytest.fail("TEST_POSTGRES_URL must point at a local throwaway database")

    engine = create_engine(Settings(database_url=POSTGRES_URL).database_url)
    with engine.begin() as connection:
        connection.execute(text("DROP SCHEMA public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))
    engine.dispose()

    monkeypatch.setenv("DATABASE_URL", POSTGRES_URL)
    return POSTGRES_URL
