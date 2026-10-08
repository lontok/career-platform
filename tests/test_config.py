import pytest

from app.core.config import Settings


@pytest.mark.parametrize(
    "raw_url",
    [
        "postgres://user:secret@db.internal:5432/railway",
        "postgresql://user:secret@db.internal:5432/railway",
    ],
)
def test_postgres_urls_use_the_psycopg_driver(raw_url: str) -> None:
    settings = Settings(database_url=raw_url)

    assert (
        settings.database_url
        == "postgresql+psycopg://user:secret@db.internal:5432/railway"
    )


@pytest.mark.parametrize(
    "url",
    [
        "postgresql+psycopg://user:secret@db.internal:5432/railway",
        "sqlite:///./data/resume.db",
        "sqlite+pysqlite:////tmp/resume-test.db",
    ],
)
def test_other_urls_are_unchanged(url: str) -> None:
    assert Settings(database_url=url).database_url == url


def test_railway_refuses_a_sqlite_database(monkeypatch) -> None:
    monkeypatch.setenv("RAILWAY_ENVIRONMENT_ID", "production-environment")

    with pytest.raises(ValueError, match="must point at Postgres on Railway"):
        Settings(database_url="sqlite:///./data/resume.db")


def test_railway_accepts_a_postgres_database(monkeypatch) -> None:
    monkeypatch.setenv("RAILWAY_ENVIRONMENT_ID", "production-environment")

    settings = Settings(
        database_url="postgresql://user:secret@db.internal:5432/railway"
    )

    assert settings.database_url.startswith("postgresql+psycopg://")
