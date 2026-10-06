from __future__ import annotations

from collections import Counter
from datetime import date
from pathlib import Path

from pydantic import ValidationError
from sqlalchemy import select, update

from app.core.urls import normalize_http_url
from app.db.session import SessionLocal
from app.models import (
    Education,
    Experience,
    ExperienceAccomplishment,
    Profile,
    Project,
    Skill,
)
from app.schemas import RequiredProfile, load_fallback_profile

FALLBACK_PROFILE_PATH = Path(__file__).resolve().parent / "fallback_profile.json"

SEED_PROFILE = {
    "seed_key": "profile:primary",
    "full_name": "Greg Lontok",
    "headline": (
        "Clinical Associate Professor - Information Systems & Business Analytics "
        "at Loyola Marymount University"
    ),
    "summary": (
        "Spent more than a decade leading technology and data science teams in "
        "Los Angeles media and advertising, then brought that experience to "
        "teaching information systems and business analytics at LMU."
    ),
    "location": "Los Angeles Metropolitan Area",
    # Left empty on purpose: the site should not read as a job search.
    "target_roles": "",
    "email": "",
    "linkedin_url": "https://www.linkedin.com/in/lontok",
    "github_url": None,
    "published": True,
}

SEED_SKILLS = [
    {
        "seed_key": "skill:affiliate-marketing",
        "name": "Affiliate Marketing",
        "category": "marketing",
        "context": None,
        "display_order": 1,
        "published": True,
    },
    {
        "seed_key": "skill:social-media-marketing",
        "name": "Social Media Marketing",
        "category": "marketing",
        "context": None,
        "display_order": 2,
        "published": True,
    },
    {
        "seed_key": "skill:sem",
        "name": "SEM",
        "category": "marketing",
        "context": None,
        "display_order": 3,
        "published": True,
    },
    {
        "seed_key": "skill:professional-scrum-master-i",
        "name": "Professional Scrum Master I (PSM I)",
        "category": "certifications",
        "context": None,
        "display_order": 4,
        "published": True,
    },
]

SEED_EXPERIENCES = [
    {
        "seed_key": "experience:lmu:clinical-associate-professor",
        "role_title": "Clinical Associate Professor - Information Systems & Business Analytics",
        "organization": "Loyola Marymount University",
        "location": "Los Angeles, CA",
        "start_date": date(2026, 6, 1),
        "end_date": None,
        "is_current": True,
        "summary": "",
        "display_order": 1,
        "published": True,
        "featured": False,
        "skill_names": [],
        "accomplishments": [],
    },
    {
        "seed_key": "experience:lmu:clinical-assistant-professor",
        "role_title": "Clinical Assistant Professor - Information Systems & Business Analytics",
        "organization": "Loyola Marymount University",
        "location": "Los Angeles, CA",
        "start_date": date(2019, 8, 1),
        "end_date": date(2026, 6, 1),
        "is_current": False,
        "summary": "",
        "display_order": 2,
        "published": True,
        "featured": False,
        "skill_names": [],
        "accomplishments": [],
    },
    {
        "seed_key": "experience:lmu:lecturer",
        "role_title": "Lecturer - Information Systems & Business Analytics",
        "organization": "Loyola Marymount University",
        "location": "Los Angeles, CA",
        "start_date": date(2018, 1, 1),
        "end_date": date(2019, 8, 1),
        "is_current": False,
        "summary": "",
        "display_order": 3,
        "published": True,
        "featured": False,
        "skill_names": [],
        "accomplishments": [],
    },
    {
        "seed_key": "experience:globalwide-media:vp-technology-data-science",
        "role_title": "VP Technology and Data Science",
        "organization": "GlobalWide Media",
        "location": "Westlake Village, CA",
        "start_date": date(2007, 1, 1),
        "end_date": date(2018, 2, 1),
        "is_current": False,
        "summary": "",
        "display_order": 4,
        "published": True,
        "featured": False,
        "skill_names": [],
        "accomplishments": [],
    },
    {
        "seed_key": "experience:valueclick:development-manager",
        "role_title": "Development Manager",
        "organization": "ValueClick",
        "location": "Westlake Village, CA",
        "start_date": date(2004, 1, 1),
        "end_date": date(2006, 12, 1),
        "is_current": False,
        "summary": "",
        "display_order": 5,
        "published": True,
        "featured": False,
        "skill_names": [],
        "accomplishments": [],
    },
    {
        "seed_key": "experience:hispeed-media:vp-engineering-it",
        "role_title": "VP of Engineering and Information Technology",
        "organization": "HiSpeed Media",
        "location": "Los Angeles, CA",
        "start_date": date(2002, 7, 1),
        "end_date": date(2006, 12, 1),
        "is_current": False,
        "summary": "",
        "display_order": 6,
        "published": True,
        "featured": False,
        "skill_names": [],
        "accomplishments": [],
    },
    {
        "seed_key": "experience:aesop-marketing:web-developer-sysadmin",
        "role_title": "Web Developer / System Administrator",
        "organization": "Aesop Marketing",
        "location": "Hollywood, CA",
        "start_date": date(2000, 1, 1),
        "end_date": date(2002, 1, 1),
        "is_current": False,
        "summary": "",
        "display_order": 7,
        "published": True,
        "featured": False,
        "skill_names": [],
        "accomplishments": [],
    },
]

SEED_PROJECTS: list[dict] = []

SEED_EDUCATION = [
    {
        "seed_key": "education:regis-university:data-science-ms",
        "institution_name": "Regis University",
        "degree_or_program": "MS",
        "field_of_study": "Data Science",
        "start_date": date(2018, 1, 1),
        "end_date": date(2020, 1, 1),
        "gpa": None,
        "honors": None,
        "relevant_coursework": None,
        "certifications": None,
        "published": True,
        "display_order": 1,
    },
    {
        "seed_key": "education:loyola-marymount-university:business-administration-ba",
        "institution_name": "Loyola Marymount University",
        "degree_or_program": "BA",
        "field_of_study": "Business Administration (MIS)",
        "start_date": date(1997, 1, 1),
        "end_date": date(2001, 1, 1),
        "gpa": None,
        "honors": None,
        "relevant_coursework": None,
        "certifications": None,
        "published": True,
        "display_order": 2,
    },
]


def validate_seed_data() -> None:
    _ensure_required_profile_fields()
    _ensure_unique_project_slugs()
    _ensure_seed_keys()
    _ensure_valid_references()
    _ensure_valid_dates()
    _ensure_valid_project_urls()


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


def _ensure_required_profile_fields() -> None:
    try:
        RequiredProfile.model_validate(
            {
                field: SEED_PROFILE[field]
                for field in (
                    "full_name",
                    "headline",
                    "summary",
                    "location",
                    "target_roles",
                )
            }
        )
    except ValidationError as exc:
        field = exc.errors()[0]["loc"][0]
        raise ValueError(f"Seed profile is missing {field}") from exc


def _ensure_unique_project_slugs() -> None:
    slug_counts = Counter(project["slug"] for project in SEED_PROJECTS)
    duplicate_slugs = sorted(slug for slug, count in slug_counts.items() if count > 1)
    if duplicate_slugs:
        raise ValueError(f"Duplicate project slug: {duplicate_slugs[0]}")


def _ensure_seed_keys() -> None:
    seed_collections = (
        ("profile", [SEED_PROFILE]),
        ("skill", SEED_SKILLS),
        ("experience", SEED_EXPERIENCES),
        ("project", SEED_PROJECTS),
        ("education", SEED_EDUCATION),
    )
    for collection_name, collection in seed_collections:
        seed_keys = [record.get("seed_key") for record in collection]
        if any(not isinstance(seed_key, str) or not seed_key for seed_key in seed_keys):
            raise ValueError(f"Missing seed key for {collection_name}")

        duplicate_keys = sorted(
            seed_key for seed_key, count in Counter(seed_keys).items() if count > 1
        )
        if duplicate_keys:
            raise ValueError(
                f"Duplicate seed key for {collection_name}: {duplicate_keys[0]}"
            )


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


def _ensure_valid_project_urls() -> None:
    for project in SEED_PROJECTS:
        for field in ("repository_url", "live_demo_url"):
            value = project[field]
            if value is not None and normalize_http_url(value) is None:
                raise ValueError(f"Invalid project URL: {field} for {project['slug']}")


def _upsert_profile(session) -> Profile:
    profile = session.scalar(
        select(Profile).where(Profile.seed_key == SEED_PROFILE["seed_key"]).limit(1)
    )

    published_profiles = update(Profile).where(Profile.published.is_(True))
    if profile is not None:
        published_profiles = published_profiles.where(Profile.id != profile.id)
    session.execute(published_profiles.values(published=False))

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
        skill = session.scalar(
            select(Skill).where(Skill.seed_key == payload["seed_key"]).limit(1)
        )
        if skill is None:
            skill = Skill(**payload)
            session.add(skill)
        else:
            for field, value in payload.items():
                setattr(skill, field, value)
        skills_by_name[payload["name"]] = skill
    _unpublish_missing_seed_records(session, Skill, SEED_SKILLS)
    return skills_by_name


def _upsert_experiences(session, skills_by_name: dict[str, Skill]) -> None:
    for payload in SEED_EXPERIENCES:
        experience = session.scalar(
            select(Experience)
            .where(Experience.seed_key == payload["seed_key"])
            .limit(1)
        )
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
    _unpublish_missing_seed_records(session, Experience, SEED_EXPERIENCES)


def _upsert_projects(session, skills_by_name: dict[str, Skill]) -> None:
    for payload in SEED_PROJECTS:
        project = session.scalar(
            select(Project).where(Project.seed_key == payload["seed_key"]).limit(1)
        )
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
    _unpublish_missing_seed_records(session, Project, SEED_PROJECTS)


def _upsert_education(session) -> None:
    for payload in SEED_EDUCATION:
        education = session.scalar(
            select(Education).where(Education.seed_key == payload["seed_key"]).limit(1)
        )
        if education is None:
            session.add(Education(**payload))
            continue

        for field, value in payload.items():
            setattr(education, field, value)
    _unpublish_missing_seed_records(session, Education, SEED_EDUCATION)


def _unpublish_missing_seed_records(session, model, seed_records) -> None:
    active_seed_keys = [record["seed_key"] for record in seed_records]
    session.execute(
        update(model)
        .where(
            model.seed_key.is_not(None),
            model.seed_key.not_in(active_seed_keys),
        )
        .values(published=False)
    )


if __name__ == "__main__":
    main()
