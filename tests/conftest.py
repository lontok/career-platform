from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.base import Base
from app.seed import seed_demo_content


@pytest.fixture
def app(monkeypatch, tmp_path) -> Iterator[FastAPI]:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'resume-test.db'}"
    monkeypatch.setenv("DATABASE_URL", database_url)

    from app.main import create_app

    application = create_app()
    Base.metadata.create_all(application.state.database_engine)

    try:
        yield application
    finally:
        application.state.database_engine.dispose()


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def session(app: FastAPI) -> Iterator[Session]:
    with app.state.session_factory() as database_session:
        yield database_session


@pytest.fixture
def sample_seed(monkeypatch) -> None:
    """Swap the real seed content for the fictional sample resume."""
    from app import seed as seed_module
    from tests import seed_samples

    for name in ("PROFILE", "SKILLS", "EXPERIENCES", "PROJECTS", "EDUCATION"):
        monkeypatch.setattr(
            seed_module, f"SEED_{name}", getattr(seed_samples, f"SAMPLE_{name}")
        )


@pytest.fixture
def seeded_session(app: FastAPI, sample_seed) -> Iterator[Session]:
    seed_demo_content(session_factory=app.state.session_factory)

    with app.state.session_factory() as database_session:
        yield database_session
