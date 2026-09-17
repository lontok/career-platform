from __future__ import annotations

from collections import Counter
from datetime import date
from pathlib import Path

from sqlalchemy import bindparam, select

from app.db.session import SessionLocal
from app.models import (
    Education,
    Experience,
    ExperienceAccomplishment,
    Profile,
    Project,
    Skill,
)
from app.schemas import load_fallback_profile

FALLBACK_PROFILE_PATH = Path(__file__).resolve().parent / "fallback_profile.json"

SEED_PROFILE = {
    "full_name": "Alex Parker",
    "headline": "Analytics-focused software builder for business teams",
    "summary": (
        "Builds dependable data products and automation that help business "
        "partners make faster, better-informed decisions."
    ),
    "location": "Los Angeles, CA",
    "target_roles": "Analytics Engineer, Data Analyst, Business Systems Analyst",
    "email": "alex.parker@example.com",
    "linkedin_url": "https://www.linkedin.com/in/alexparker-analytics",
    "github_url": "https://github.com/alexparker-analytics",
    "published": True,
}

SEED_SKILLS = [
    {
        "name": "SQL",
        "category": "analytics",
        "context": "Warehouse modeling, QA, and decision support.",
        "display_order": 1,
        "published": True,
    },
    {
        "name": "Python",
        "category": "programming",
        "context": "Automation, data services, and testing.",
        "display_order": 2,
        "published": True,
    },
]

SEED_EXPERIENCES = [
    {
        "role_title": "Analytics Engineering Intern",
        "organization": "West Coast Commerce",
        "location": "Los Angeles, CA",
        "start_date": date(2026, 6, 1),
        "end_date": None,
        "is_current": True,
        "summary": "Supported reporting automation and data quality initiatives.",
        "display_order": 1,
        "published": True,
        "skill_names": ["SQL", "Python"],
        "accomplishments": [
            {
                "statement": "Automated weekly KPI reporting for business stakeholders.",
                "metric": "6 hours saved per week",
                "display_order": 1,
            }
        ],
    }
]

SEED_PROJECTS = [
    {
        "slug": "career-platform",
        "title": "Career Platform Resume Site",
        "summary": "Database-driven resume content for analytics-focused roles.",
        "problem": "Resume updates were slow and duplicated across pages.",
        "contribution": "Designed the content model, seed flow, and read service.",
        "methods": "FastAPI, SQLAlchemy, SQLite, pytest",
        "outcome": "Created a maintainable content workflow for future public pages.",
        "repository_url": None,
        "live_demo_url": None,
        "published": True,
        "featured": True,
        "display_order": 1,
        "skill_names": ["SQL", "Python"],
    }
]

SEED_EDUCATION = [
    {
        "institution_name": "California State University",
        "degree_or_program": "B.S.",
        "field_of_study": "Information Systems",
        "start_date": date(2022, 8, 22),
        "end_date": date(2026, 5, 18),
        "gpa": "3.8",
        "honors": "Dean's List",
        "relevant_coursework": "Database Systems, Business Analytics, Statistics",
        "certifications": None,
        "published": True,
        "display_order": 1,
    }
]


def validate_seed_data() -> None:
    _ensure_unique_project_slugs()
    _ensure_valid_references()
    _ensure_valid_dates()


def seed_demo_content(
    session_factory=SessionLocal, fallback_path: Path = FALLBACK_PROFILE_PATH
) -> None:
    load_fallback_profile(fallback_path)
    validate_seed_data()

    with session_factory() as session:
        skills_by_name = _upsert_skills(session)
        _upsert_profile(session)
        _upsert_experiences(session, skills_by_name)
        _upsert_projects(session, skills_by_name)
        _upsert_education(session)
        session.commit()


def main() -> None:
    seed_demo_content()
    print("Seeded published resume content.")


def _ensure_unique_project_slugs() -> None:
    slug_counts = Counter(project["slug"] for project in SEED_PROJECTS)
    duplicate_slugs = sorted(slug for slug, count in slug_counts.items() if count > 1)
    if duplicate_slugs:
        raise ValueError(f"Duplicate project slug: {duplicate_slugs[0]}")


def _ensure_valid_references() -> None:
    known_skills = {skill["name"] for skill in SEED_SKILLS}
    for source_name, collection in (
        ("experience", SEED_EXPERIENCES),
        ("project", SEED_PROJECTS),
    ):
        for record in collection:
            for skill_name in record.get("skill_names", []):
                if skill_name not in known_skills:
                    raise ValueError(
                        f"Unknown skill reference: {skill_name} in {source_name}"
                    )


def _ensure_valid_dates() -> None:
    for experience in SEED_EXPERIENCES:
        end_date = experience["end_date"]
        if end_date and end_date < experience["start_date"]:
            raise ValueError(
                f"Experience {experience['role_title']} has an end date before start date"
            )
        if experience["is_current"] and end_date is not None:
            raise ValueError(
                f"Current experience {experience['role_title']} must not define an end date"
            )

    for education in SEED_EDUCATION:
        end_date = education["end_date"]
        if end_date and end_date < education["start_date"]:
            raise ValueError(
                f"Education {education['institution_name']} has an end date before start date"
            )


def _upsert_profile(session) -> Profile:
    statement = select(Profile).where(Profile.email == bindparam("email")).limit(1)
    profile = session.execute(
        statement, {"email": SEED_PROFILE["email"]}
    ).scalar_one_or_none()
    if profile is None:
        profile = Profile(**SEED_PROFILE)
        session.add(profile)
    else:
        for field, value in SEED_PROFILE.items():
            setattr(profile, field, value)
    return profile


def _upsert_skills(session) -> dict[str, Skill]:
    skills_by_name: dict[str, Skill] = {}
    for payload in SEED_SKILLS:
        statement = select(Skill).where(Skill.name == bindparam("name")).limit(1)
        skill = session.execute(
            statement, {"name": payload["name"]}
        ).scalar_one_or_none()
        if skill is None:
            skill = Skill(**payload)
            session.add(skill)
        else:
            for field, value in payload.items():
                setattr(skill, field, value)
        skills_by_name[payload["name"]] = skill
    return skills_by_name


def _upsert_experiences(session, skills_by_name: dict[str, Skill]) -> None:
    for payload in SEED_EXPERIENCES:
        identity = {
            "role_title": payload["role_title"],
            "organization": payload["organization"],
            "start_date": payload["start_date"],
        }
        statement = (
            select(Experience)
            .where(
                Experience.role_title == bindparam("role_title"),
                Experience.organization == bindparam("organization"),
                Experience.start_date == bindparam("start_date"),
            )
            .limit(1)
        )
        experience = session.execute(statement, identity).scalar_one_or_none()
        core_fields = {
            key: value
            for key, value in payload.items()
            if key not in {"skill_names", "accomplishments"}
        }

        if experience is None:
            experience = Experience(**core_fields)
            session.add(experience)
        else:
            for field, value in core_fields.items():
                setattr(experience, field, value)

        experience.skills = [skills_by_name[name] for name in payload["skill_names"]]
        experience.accomplishments.clear()
        for accomplishment_payload in payload["accomplishments"]:
            experience.accomplishments.append(
                ExperienceAccomplishment(**accomplishment_payload)
            )


def _upsert_projects(session, skills_by_name: dict[str, Skill]) -> None:
    for payload in SEED_PROJECTS:
        statement = select(Project).where(Project.slug == bindparam("slug")).limit(1)
        project = session.execute(
            statement, {"slug": payload["slug"]}
        ).scalar_one_or_none()
        core_fields = {
            key: value for key, value in payload.items() if key != "skill_names"
        }

        if project is None:
            project = Project(**core_fields)
            session.add(project)
        else:
            for field, value in core_fields.items():
                setattr(project, field, value)

        project.skills = [skills_by_name[name] for name in payload["skill_names"]]


def _upsert_education(session) -> None:
    for payload in SEED_EDUCATION:
        identity = {
            "institution_name": payload["institution_name"],
            "degree_or_program": payload["degree_or_program"],
            "start_date": payload["start_date"],
        }
        statement = (
            select(Education)
            .where(
                Education.institution_name == bindparam("institution_name"),
                Education.degree_or_program == bindparam("degree_or_program"),
                Education.start_date == bindparam("start_date"),
            )
            .limit(1)
        )
        education = session.execute(statement, identity).scalar_one_or_none()
        if education is None:
            session.add(Education(**payload))
            continue

        for field, value in payload.items():
            setattr(education, field, value)


if __name__ == "__main__":
    main()
