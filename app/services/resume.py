from __future__ import annotations

import logging
from pathlib import Path

from sqlalchemy import bindparam, select
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.orm import selectinload, with_loader_criteria

from app.core.urls import normalize_http_url
from app.db.session import SessionLocal
from app.models import Education, Experience, Profile, Project, Skill
from app.schemas import HomepageContent, PublicProfile, load_fallback_profile

logger = logging.getLogger(__name__)

FALLBACK_PROFILE_PATH = Path(__file__).resolve().parent.parent / "fallback_profile.json"
HOMEPAGE_OUTAGE_MESSAGE = "Detailed resume information is temporarily unavailable."


class DatabaseUnavailableError(RuntimeError):
    """Raised when published resume content cannot be read from the database."""


class ResumeService:
    def __init__(
        self,
        session_factory=SessionLocal,
        fallback_profile_path: Path = FALLBACK_PROFILE_PATH,
    ) -> None:
        self._session_factory = session_factory
        self._fallback_profile_path = fallback_profile_path

    def get_homepage(self) -> HomepageContent:
        try:
            with self._session_factory() as session:
                profile = session.execute(
                    select(Profile)
                    .where(Profile.published.is_(True))
                    .order_by(Profile.id.asc())
                    .limit(1)
                ).scalar_one_or_none()
                experiences = session.execute(self._experience_query()).scalars().all()
                projects = (
                    session.execute(self._homepage_project_query()).scalars().all()
                )
                skills = session.execute(self._skill_query()).scalars().all()
                education = session.execute(self._education_query()).scalars().all()
        except (OperationalError, SQLAlchemyError):
            logger.exception("Unable to load homepage content from the database")
            return HomepageContent(
                profile=load_fallback_profile(self._fallback_profile_path),
                experiences=[],
                projects=[],
                skills=[],
                education=[],
                is_fallback=True,
                outage_message=HOMEPAGE_OUTAGE_MESSAGE,
            )

        return HomepageContent(
            profile=PublicProfile.from_profile(profile) if profile else None,
            experiences=experiences,
            projects=self._sanitize_project_urls(projects),
            skills=skills,
            education=education,
        )

    def get_experiences(self) -> list[Experience]:
        try:
            with self._session_factory() as session:
                return session.execute(self._experience_query()).scalars().all()
        except (OperationalError, SQLAlchemyError) as exc:
            logger.exception("Unable to load published experiences")
            raise DatabaseUnavailableError(
                "Published experiences are unavailable"
            ) from exc

    def get_projects(self) -> list[Project]:
        try:
            with self._session_factory() as session:
                projects = session.execute(self._project_query()).scalars().all()
        except (OperationalError, SQLAlchemyError) as exc:
            logger.exception("Unable to load published projects")
            raise DatabaseUnavailableError(
                "Published projects are unavailable"
            ) from exc
        return self._sanitize_project_urls(projects)

    def get_skills(self) -> list[Skill]:
        try:
            with self._session_factory() as session:
                return session.execute(self._skill_query()).scalars().all()
        except (OperationalError, SQLAlchemyError) as exc:
            logger.exception("Unable to load published skills")
            raise DatabaseUnavailableError("Published skills are unavailable") from exc

    def get_education(self) -> list[Education]:
        try:
            with self._session_factory() as session:
                return session.execute(self._education_query()).scalars().all()
        except (OperationalError, SQLAlchemyError) as exc:
            logger.exception("Unable to load published education")
            raise DatabaseUnavailableError(
                "Published education is unavailable"
            ) from exc

    def get_project_by_slug(self, slug: str) -> Project | None:
        statement = (
            select(Project)
            .options(
                selectinload(Project.skills),
                self._published_skill_loader(),
            )
            .where(
                Project.slug == bindparam("slug"),
                Project.published.is_(True),
            )
            .order_by(Project.id.asc())
            .limit(1)
        )

        try:
            with self._session_factory() as session:
                project = session.execute(
                    statement, {"slug": slug}
                ).scalar_one_or_none()
        except (OperationalError, SQLAlchemyError) as exc:
            logger.exception("Unable to load published project for slug=%s", slug)
            raise DatabaseUnavailableError("Published project is unavailable") from exc
        return self._sanitize_project_urls([project])[0] if project else None

    @staticmethod
    def _sanitize_project_urls(projects: list[Project]) -> list[Project]:
        for project in projects:
            project.repository_url = normalize_http_url(project.repository_url)
            project.live_demo_url = normalize_http_url(project.live_demo_url)
        return projects

    @staticmethod
    def _experience_query():
        return (
            select(Experience)
            .options(
                selectinload(Experience.accomplishments),
                selectinload(Experience.skills),
                ResumeService._published_skill_loader(),
            )
            .where(Experience.published.is_(True))
            .order_by(
                Experience.is_current.desc(),
                Experience.start_date.desc(),
                Experience.display_order.asc(),
                Experience.id.asc(),
            )
        )

    @staticmethod
    def _homepage_project_query():
        return (
            select(Project)
            .options(
                selectinload(Project.skills),
                ResumeService._published_skill_loader(),
            )
            .where(Project.published.is_(True), Project.featured.is_(True))
            .order_by(Project.display_order.asc(), Project.id.asc())
        )

    @staticmethod
    def _project_query():
        return (
            select(Project)
            .options(
                selectinload(Project.skills),
                ResumeService._published_skill_loader(),
            )
            .where(Project.published.is_(True))
            .order_by(Project.display_order.asc(), Project.id.asc())
        )

    @staticmethod
    def _published_skill_loader():
        return with_loader_criteria(
            Skill,
            Skill.published.is_(True),
            include_aliases=True,
        )

    @staticmethod
    def _skill_query():
        return (
            select(Skill)
            .where(Skill.published.is_(True))
            .order_by(Skill.display_order.asc(), Skill.id.asc())
        )

    @staticmethod
    def _education_query():
        return (
            select(Education)
            .where(Education.published.is_(True))
            .order_by(Education.display_order.asc(), Education.id.asc())
        )
