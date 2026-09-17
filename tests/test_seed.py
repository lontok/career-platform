from __future__ import annotations

from copy import deepcopy
from datetime import date

import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from app import seed as seed_module
from app.db.base import Base
from app.db.session import register_sqlite_foreign_keys
from app.models import (
    Education,
    Experience,
    ExperienceAccomplishment,
    Profile,
    Project,
    Skill,
)
from app.schemas.content import FallbackProfile
from app.services.resume import ResumeService


@pytest.fixture()
def session_factory():
    register_sqlite_foreign_keys()
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    try:
        yield factory
    finally:
        engine.dispose()


def test_fallback_profile_rejects_invalid_urls_unknown_fields_and_empty_links() -> None:
    valid_payload = {
        "full_name": "Public Candidate",
        "headline": "Analytics engineer",
        "summary": "Builds reliable data products.",
        "location": "Los Angeles, CA",
        "target_roles": ["Analytics Engineer", "Data Analyst"],
        "contact_links": [
            {
                "label": "LinkedIn",
                "url": "https://www.linkedin.com/in/public-candidate",
            }
        ],
    }

    with pytest.raises(ValidationError):
        FallbackProfile.model_validate({**valid_payload, "contact_links": []})

    with pytest.raises(ValidationError):
        FallbackProfile.model_validate(
            {
                **valid_payload,
                "contact_links": [{"label": "Profile", "url": "ftp://example.com"}],
            }
        )

    with pytest.raises(ValidationError):
        FallbackProfile.model_validate({**valid_payload, "unexpected": "value"})


def test_seed_demo_content_validates_fallback_before_writing(
    session_factory, monkeypatch
) -> None:
    def raising_fallback_loader(_path):
        raise ValueError("fallback profile is invalid")

    monkeypatch.setattr(seed_module, "load_fallback_profile", raising_fallback_loader)

    with pytest.raises(ValueError, match="fallback profile is invalid"):
        seed_module.seed_demo_content(session_factory=session_factory)

    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(Profile)) == 0


def test_seed_demo_content_creates_published_records_and_is_idempotent(
    session_factory,
) -> None:
    seed_module.seed_demo_content(session_factory=session_factory)
    seed_module.seed_demo_content(session_factory=session_factory)

    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(Profile)) == 1
        assert session.scalar(select(func.count()).select_from(Experience)) == 1
        assert (
            session.scalar(select(func.count()).select_from(ExperienceAccomplishment))
            == 1
        )
        assert session.scalar(select(func.count()).select_from(Project)) == 1
        assert session.scalar(select(func.count()).select_from(Skill)) >= 1
        assert session.scalar(select(func.count()).select_from(Education)) == 1

        profile = session.execute(
            select(Profile).where(Profile.published.is_(True))
        ).scalar_one()
        project = session.execute(
            select(Project).where(Project.published.is_(True))
        ).scalar_one()

        assert profile.full_name == seed_module.SEED_PROFILE["full_name"]
        assert project.slug == seed_module.SEED_PROJECTS[0]["slug"]
        assert project.featured is True
        assert project.published is True


def test_seed_updates_stable_records_when_profile_email_and_experience_date_change(
    session_factory, monkeypatch
) -> None:
    seed_module.seed_demo_content(session_factory=session_factory)

    changed_profile = {
        **seed_module.SEED_PROFILE,
        "email": "alex.parker.updated@example.com",
    }
    changed_experiences = deepcopy(seed_module.SEED_EXPERIENCES)
    changed_experiences[0]["start_date"] = date(2026, 7, 1)
    monkeypatch.setattr(seed_module, "SEED_PROFILE", changed_profile)
    monkeypatch.setattr(seed_module, "SEED_EXPERIENCES", changed_experiences)

    seed_module.seed_demo_content(session_factory=session_factory)

    with session_factory() as session:
        profiles = session.scalars(select(Profile).order_by(Profile.id)).all()
        experiences = session.scalars(select(Experience).order_by(Experience.id)).all()

        assert [(profile.email, profile.published) for profile in profiles] == [
            ("alex.parker.updated@example.com", True)
        ]
        assert [
            (experience.start_date, experience.published) for experience in experiences
        ] == [(date(2026, 7, 1), True)]

    homepage = ResumeService(session_factory=session_factory).get_homepage()
    assert homepage.profile is not None
    assert homepage.profile.email == "alex.parker.updated@example.com"
    assert [experience.start_date for experience in homepage.experiences] == [
        date(2026, 7, 1)
    ]


def test_seed_unpublishes_seed_managed_records_removed_from_seed_data(
    session_factory, monkeypatch
) -> None:
    seed_module.seed_demo_content(session_factory=session_factory)
    monkeypatch.setattr(seed_module, "SEED_SKILLS", [])
    monkeypatch.setattr(seed_module, "SEED_EXPERIENCES", [])
    monkeypatch.setattr(seed_module, "SEED_PROJECTS", [])
    monkeypatch.setattr(seed_module, "SEED_EDUCATION", [])

    seed_module.seed_demo_content(session_factory=session_factory)

    homepage = ResumeService(session_factory=session_factory).get_homepage()
    assert homepage.profile is not None
    assert homepage.experiences == []
    assert homepage.projects == []
    assert homepage.skills == []
    assert homepage.education == []

    with session_factory() as session:
        assert (
            session.scalar(
                select(func.count()).select_from(Experience).where(Experience.published)
            )
            == 0
        )
        assert (
            session.scalar(
                select(func.count()).select_from(Project).where(Project.published)
            )
            == 0
        )
        assert (
            session.scalar(
                select(func.count()).select_from(Skill).where(Skill.published)
            )
            == 0
        )
        assert (
            session.scalar(
                select(func.count()).select_from(Education).where(Education.published)
            )
            == 0
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("repository_url", "javascript:alert(1)"),
        ("live_demo_url", "data:text/html,unsafe"),
        ("repository_url", "not a valid URL"),
    ],
)
def test_seed_rejects_unsafe_project_urls_before_writing(
    session_factory, monkeypatch, field: str, value: str
) -> None:
    invalid_projects = deepcopy(seed_module.SEED_PROJECTS)
    invalid_projects[0][field] = value
    monkeypatch.setattr(seed_module, "SEED_PROJECTS", invalid_projects)

    with pytest.raises(ValueError, match="Invalid project URL"):
        seed_module.seed_demo_content(session_factory=session_factory)

    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(Project)) == 0


def test_seed_demo_content_rejects_duplicate_project_slugs_before_commit(
    session_factory, monkeypatch
) -> None:
    duplicate_projects = deepcopy(seed_module.SEED_PROJECTS)
    duplicate_projects.append(
        {
            **duplicate_projects[0],
            "title": "Duplicate project",
        }
    )
    monkeypatch.setattr(seed_module, "SEED_PROJECTS", duplicate_projects)

    with pytest.raises(ValueError, match="Duplicate project slug"):
        seed_module.seed_demo_content(session_factory=session_factory)

    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(Project)) == 0


def test_seed_demo_content_rejects_unknown_skill_references_before_commit(
    session_factory, monkeypatch
) -> None:
    invalid_experiences = deepcopy(seed_module.SEED_EXPERIENCES)
    invalid_experiences[0]["skill_names"] = ["Missing Skill"]
    monkeypatch.setattr(seed_module, "SEED_EXPERIENCES", invalid_experiences)

    with pytest.raises(ValueError, match="Unknown skill reference"):
        seed_module.seed_demo_content(session_factory=session_factory)

    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(Experience)) == 0
