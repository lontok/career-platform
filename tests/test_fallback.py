from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.main import create_app
from app.routers import pages
from app.seed import seed_demo_content
from app.services import DatabaseUnavailableError, ResumeService


class UnavailableProjectsService:
    def get_projects(self) -> list[object]:
        raise DatabaseUnavailableError("sqlite database connection failed")


def unavailable_service() -> UnavailableProjectsService:
    return UnavailableProjectsService()


def test_database_failure_on_projects_is_generic_503(client, app) -> None:
    app.dependency_overrides[pages.get_resume_service] = unavailable_service

    response = client.get("/projects")

    assert response.status_code == 503
    assert "temporarily unavailable" in response.text.lower()
    assert "sqlite" not in response.text.lower()


def test_homepage_fallback_omits_detailed_resume_content(client, app) -> None:
    def unavailable_session_factory():
        raise OperationalError("SELECT 1", {}, RuntimeError("database offline"))

    app.dependency_overrides[pages.get_resume_service] = lambda: ResumeService(
        unavailable_session_factory
    )

    response = client.get("/")

    assert response.status_code == 200
    assert "Detailed resume information is temporarily unavailable." in response.text
    assert "Featured Projects" not in response.text
    assert 'href="/experience"' not in response.text


def test_page_dependency_uses_database_url_configured_before_app_creation(
    monkeypatch, tmp_path: Path
) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'configured-before-app.db'}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    seed_demo_content(session_factory=session_factory)

    try:
        with TestClient(create_app()) as client:
            response = client.get("/projects")
    finally:
        engine.dispose()

    assert response.status_code == 200
    assert "Career Platform Resume Site" in response.text
