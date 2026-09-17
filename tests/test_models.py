import importlib
from datetime import date

from sqlalchemy import text

from app.db.base import Base
from app.models.experience import Experience, ExperienceAccomplishment
from app.models.project import Project
from app.models.skill import Skill


def test_project_can_have_skills() -> None:
    project = Project(
        slug="revenue-dashboard",
        title="Revenue Dashboard",
        summary="Dashboard for weekly sales decisions.",
        problem="Sales reporting was delayed.",
        contribution="Built the reporting model.",
        methods="SQL and Python",
        published=True,
    )
    skill = Skill(name="SQL", category="analytics", published=True)

    project.skills.append(skill)

    assert project.skills == [skill]


def test_session_local_enables_sqlite_foreign_keys(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")

    session_module = importlib.import_module("app.db.session")
    session_module = importlib.reload(session_module)

    with session_module.SessionLocal() as session:
        foreign_keys = session.execute(text("PRAGMA foreign_keys")).scalar_one()

    assert foreign_keys == 1


def test_deleting_experience_cascades_accomplishments(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")

    session_module = importlib.import_module("app.db.session")
    session_module = importlib.reload(session_module)
    Base.metadata.create_all(session_module.engine)

    with session_module.SessionLocal() as session:
        experience = Experience(
            role_title="Business Analyst Intern",
            organization="Acme Corp",
            location="Los Angeles, CA",
            start_date=date(2025, 6, 1),
            end_date=date(2025, 8, 31),
            is_current=False,
            summary="Supported reporting improvements.",
            published=True,
        )
        experience.accomplishments.append(
            ExperienceAccomplishment(
                statement="Reduced manual reporting effort.",
                metric="4 hours per week",
            )
        )

        session.add(experience)
        session.commit()
        accomplishment_id = experience.accomplishments[0].id

        session.delete(experience)
        session.commit()

        assert session.get(ExperienceAccomplishment, accomplishment_id) is None
