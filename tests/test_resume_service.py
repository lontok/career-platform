from __future__ import annotations

from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker

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
from app.services.resume import DatabaseUnavailableError, ResumeService


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


def test_homepage_uses_fallback_only_when_database_fails() -> None:
    def raising_session_factory():
        raise OperationalError("SELECT 1", {}, RuntimeError("database offline"))

    homepage = ResumeService(session_factory=raising_session_factory).get_homepage()

    assert homepage.is_fallback is True
    assert homepage.profile is not None
    assert homepage.profile.headline
    assert homepage.experiences == []
    assert homepage.projects == []
    assert homepage.skills == []
    assert homepage.education == []


def test_homepage_does_not_use_fallback_for_successful_empty_database(
    session_factory,
) -> None:
    homepage = ResumeService(session_factory=session_factory).get_homepage()

    assert homepage.is_fallback is False
    assert homepage.profile is None
    assert homepage.experiences == []
    assert homepage.projects == []
    assert homepage.skills == []
    assert homepage.education == []


def test_homepage_returns_only_published_content_with_expected_ordering(
    session_factory,
) -> None:
    with session_factory() as session:
        session.add_all(
            [
                Profile(
                    full_name="Public Candidate",
                    headline="Analytics engineer",
                    summary="Turns complex operations data into decisions.",
                    location="Los Angeles, CA",
                    target_roles="Analytics Engineer, Data Analyst",
                    email="public@example.com",
                    linkedin_url="https://www.linkedin.com/in/public-candidate",
                    github_url="https://github.com/public-candidate",
                    published=True,
                ),
                Profile(
                    full_name="Private Candidate",
                    headline="Hidden",
                    summary="Should never render.",
                    location="Los Angeles, CA",
                    target_roles="Hidden",
                    email="private@example.com",
                    published=False,
                ),
            ]
        )

        sql_skill = Skill(
            name="SQL",
            category="analytics",
            context="Warehouse querying",
            display_order=1,
            published=True,
        )
        python_skill = Skill(
            name="Python",
            category="programming",
            context="Automation and services",
            display_order=2,
            published=True,
        )
        hidden_skill = Skill(
            name="Stealth",
            category="private",
            display_order=3,
            published=False,
        )
        session.add_all([sql_skill, python_skill, hidden_skill])

        current_role = Experience(
            role_title="Analytics Engineer",
            organization="Current Co",
            location="Los Angeles, CA",
            start_date=date(2026, 2, 1),
            end_date=None,
            is_current=True,
            summary="Owns reporting automation.",
            published=True,
            display_order=10,
        )
        current_role.skills.extend([python_skill, sql_skill, hidden_skill])
        current_role.accomplishments.extend(
            [
                ExperienceAccomplishment(
                    statement="Built self-serve dashboards.",
                    metric="2x adoption",
                    display_order=2,
                ),
                ExperienceAccomplishment(
                    statement="Reduced manual reporting time.",
                    metric="6 hours weekly",
                    display_order=1,
                ),
            ]
        )

        recent_completed_role = Experience(
            role_title="Data Analyst",
            organization="Recent Co",
            location="Los Angeles, CA",
            start_date=date(2025, 6, 1),
            end_date=date(2026, 1, 15),
            is_current=False,
            summary="Improved executive reporting.",
            published=True,
            display_order=20,
        )
        hidden_role = Experience(
            role_title="Hidden Role",
            organization="Private Co",
            location="Los Angeles, CA",
            start_date=date(2026, 4, 1),
            end_date=None,
            is_current=True,
            summary="Should not be returned.",
            published=False,
        )
        session.add_all([current_role, recent_completed_role, hidden_role])

        session.add_all(
            [
                Project(
                    slug="featured-first",
                    title="Featured First",
                    summary="Visible project",
                    problem="Decision latency",
                    contribution="Built data app",
                    methods="FastAPI, SQLAlchemy",
                    published=True,
                    featured=True,
                    display_order=1,
                    skills=[sql_skill, hidden_skill],
                ),
                Project(
                    slug="featured-second",
                    title="Featured Second",
                    summary="Visible project",
                    problem="Reporting errors",
                    contribution="Automated QA",
                    methods="Python, tests",
                    published=True,
                    featured=True,
                    display_order=2,
                    skills=[python_skill],
                ),
                Project(
                    slug="published-but-not-featured",
                    title="Not on homepage",
                    summary="Visible elsewhere",
                    problem="Other",
                    contribution="Other",
                    methods="Other",
                    published=True,
                    featured=False,
                    display_order=3,
                ),
                Project(
                    slug="unpublished-featured",
                    title="Private featured",
                    summary="Should not show",
                    problem="Private",
                    contribution="Private",
                    methods="Private",
                    published=False,
                    featured=True,
                    display_order=0,
                ),
            ]
        )

        session.add_all(
            [
                Education(
                    institution_name="State University",
                    degree_or_program="B.S.",
                    field_of_study="Information Systems",
                    start_date=date(2022, 8, 15),
                    end_date=date(2026, 5, 15),
                    honors="Dean's List",
                    published=True,
                    display_order=2,
                ),
                Education(
                    institution_name="Community College",
                    degree_or_program="Certificate",
                    field_of_study="Data Analytics",
                    start_date=date(2021, 1, 10),
                    end_date=date(2021, 12, 15),
                    published=True,
                    display_order=1,
                ),
                Education(
                    institution_name="Hidden Academy",
                    degree_or_program="Hidden",
                    field_of_study="Hidden",
                    start_date=date(2020, 1, 1),
                    end_date=date(2020, 12, 1),
                    published=False,
                    display_order=0,
                ),
            ]
        )
        session.commit()

    homepage = ResumeService(session_factory=session_factory).get_homepage()

    assert homepage.is_fallback is False
    assert homepage.profile is not None
    assert homepage.profile.full_name == "Public Candidate"
    assert homepage.profile.contact_links[0].label == "LinkedIn"
    assert [experience.organization for experience in homepage.experiences] == [
        "Current Co",
        "Recent Co",
    ]
    assert [
        accomplishment.statement
        for accomplishment in homepage.experiences[0].accomplishments
    ] == [
        "Reduced manual reporting time.",
        "Built self-serve dashboards.",
    ]
    assert [project.slug for project in homepage.projects] == [
        "featured-first",
        "featured-second",
    ]
    assert [skill.name for skill in homepage.experiences[0].skills] == ["SQL", "Python"]
    assert [skill.name for skill in homepage.projects[0].skills] == ["SQL"]
    assert [skill.name for skill in homepage.skills] == ["SQL", "Python"]
    assert [education.institution_name for education in homepage.education] == [
        "Community College",
        "State University",
    ]


def test_published_collection_queries_filter_and_order_public_data(
    session_factory,
) -> None:
    with session_factory() as session:
        sql_skill = Skill(
            name="SQL",
            category="analytics",
            display_order=1,
            published=True,
        )
        python_skill = Skill(
            name="Python",
            category="programming",
            display_order=2,
            published=True,
        )
        hidden_skill = Skill(
            name="Hidden",
            category="private",
            display_order=0,
            published=False,
        )
        session.add_all([sql_skill, python_skill, hidden_skill])

        current_role = Experience(
            role_title="Current Role",
            organization="Current Org",
            location="Los Angeles, CA",
            start_date=date(2026, 1, 1),
            end_date=None,
            is_current=True,
            summary="Current summary",
            published=True,
        )
        current_role.skills.extend([sql_skill, hidden_skill])
        session.add_all(
            [
                current_role,
                Experience(
                    role_title="Past Role",
                    organization="Past Org",
                    location="Los Angeles, CA",
                    start_date=date(2025, 1, 1),
                    end_date=date(2025, 12, 1),
                    is_current=False,
                    summary="Past summary",
                    published=True,
                ),
                Experience(
                    role_title="Hidden Role",
                    organization="Hidden Org",
                    location="Los Angeles, CA",
                    start_date=date(2027, 1, 1),
                    end_date=None,
                    is_current=True,
                    summary="Hidden summary",
                    published=False,
                ),
            ]
        )
        session.add_all(
            [
                Project(
                    slug="second-project",
                    title="Second",
                    summary="Second summary",
                    problem="Problem",
                    contribution="Contribution",
                    methods="Methods",
                    published=True,
                    featured=False,
                    display_order=2,
                    skills=[python_skill],
                ),
                Project(
                    slug="first-project",
                    title="First",
                    summary="First summary",
                    problem="Problem",
                    contribution="Contribution",
                    methods="Methods",
                    published=True,
                    featured=False,
                    display_order=1,
                    skills=[sql_skill, hidden_skill],
                ),
                Project(
                    slug="hidden-project",
                    title="Hidden",
                    summary="Hidden summary",
                    problem="Problem",
                    contribution="Contribution",
                    methods="Methods",
                    published=False,
                    featured=False,
                    display_order=0,
                ),
            ]
        )
        session.add_all(
            [
                Education(
                    institution_name="Visible One",
                    degree_or_program="B.S.",
                    field_of_study="Analytics",
                    start_date=date(2020, 1, 1),
                    end_date=date(2024, 1, 1),
                    published=True,
                    display_order=2,
                ),
                Education(
                    institution_name="Visible Two",
                    degree_or_program="Certificate",
                    field_of_study="Data",
                    start_date=date(2019, 1, 1),
                    end_date=date(2019, 6, 1),
                    published=True,
                    display_order=1,
                ),
                Education(
                    institution_name="Hidden School",
                    degree_or_program="Hidden",
                    field_of_study="Hidden",
                    start_date=date(2018, 1, 1),
                    end_date=date(2018, 6, 1),
                    published=False,
                    display_order=0,
                ),
            ]
        )
        session.commit()

    service = ResumeService(session_factory=session_factory)

    experiences = service.get_experiences()
    assert [experience.organization for experience in experiences] == [
        "Current Org",
        "Past Org",
    ]
    assert [skill.name for skill in experiences[0].skills] == ["SQL"]
    projects = service.get_projects()
    assert [project.slug for project in projects] == [
        "first-project",
        "second-project",
    ]
    assert [skill.name for skill in projects[0].skills] == ["SQL"]
    assert [skill.name for skill in service.get_skills()] == ["SQL", "Python"]
    assert [education.institution_name for education in service.get_education()] == [
        "Visible Two",
        "Visible One",
    ]


def test_get_project_by_slug_returns_published_projects_only(session_factory) -> None:
    with session_factory() as session:
        sql_skill = Skill(
            name="SQL",
            category="analytics",
            display_order=1,
            published=True,
        )
        hidden_skill = Skill(
            name="Hidden",
            category="private",
            display_order=2,
            published=False,
        )
        session.add_all([sql_skill, hidden_skill])
        session.add_all(
            [
                Project(
                    slug="published-work",
                    title="Published",
                    summary="Visible summary",
                    problem="Visible problem",
                    contribution="Visible contribution",
                    methods="Visible methods",
                    published=True,
                    featured=False,
                    display_order=1,
                    skills=[sql_skill, hidden_skill],
                ),
                Project(
                    slug="private-work",
                    title="Private",
                    summary="Hidden summary",
                    problem="Hidden problem",
                    contribution="Hidden contribution",
                    methods="Hidden methods",
                    published=False,
                    featured=False,
                    display_order=2,
                ),
            ]
        )
        session.commit()

    service = ResumeService(session_factory=session_factory)
    published_project = service.get_project_by_slug("published-work")

    assert published_project is not None
    assert published_project.slug == "published-work"
    assert [skill.name for skill in published_project.skills] == ["SQL"]
    assert service.get_project_by_slug("private-work") is None
    assert service.get_project_by_slug("missing-project") is None


def test_project_queries_omit_unsafe_external_urls(session_factory) -> None:
    with session_factory() as session:
        session.add_all(
            [
                Project(
                    slug="unsafe-schemes",
                    title="Unsafe schemes",
                    summary="Unsafe links must not be public.",
                    problem="Unsafe links",
                    contribution="Safe rendering",
                    methods="Validation",
                    repository_url="javascript:alert(1)",
                    live_demo_url="data:text/html,unsafe",
                    published=True,
                    display_order=1,
                ),
                Project(
                    slug="malformed-url",
                    title="Malformed URL",
                    summary="Malformed links must not be public.",
                    problem="Malformed links",
                    contribution="Safe rendering",
                    methods="Validation",
                    repository_url="not a valid URL",
                    live_demo_url="https://demo.example.com",
                    published=True,
                    display_order=2,
                ),
            ]
        )
        session.commit()

    service = ResumeService(session_factory=session_factory)
    projects = service.get_projects()
    unsafe_schemes, malformed_url = projects

    assert unsafe_schemes.repository_url is None
    assert unsafe_schemes.live_demo_url is None
    assert malformed_url.repository_url is None
    assert malformed_url.live_demo_url == "https://demo.example.com/"
    assert service.get_project_by_slug("unsafe-schemes").repository_url is None


@pytest.mark.parametrize(
    ("method_name", "args"),
    [
        ("get_experiences", ()),
        ("get_projects", ()),
        ("get_skills", ()),
        ("get_education", ()),
        ("get_project_by_slug", ("known-slug",)),
    ],
)
def test_non_homepage_queries_raise_database_unavailable_error(
    method_name: str, args: tuple[str, ...]
) -> None:
    def raising_session_factory():
        raise OperationalError("SELECT 1", {}, RuntimeError("database offline"))

    service = ResumeService(session_factory=raising_session_factory)

    with pytest.raises(DatabaseUnavailableError):
        getattr(service, method_name)(*args)
