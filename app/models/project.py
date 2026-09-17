from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, ForeignKey, Index, Integer, String, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.skill import Skill


project_skills = Table(
    "project_skills",
    Base.metadata,
    Column(
        "project_id", ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True
    ),
    Column("skill_id", ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True),
)


class Project(Base):
    __tablename__ = "projects"
    __table_args__ = (
        Index("ux_projects_seed_key", "seed_key", unique=True),
        Index(
            "ix_projects_published_featured_display_order",
            "published",
            "featured",
            "display_order",
        ),
        Index("ix_projects_published_display_order", "published", "display_order"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    seed_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    summary: Mapped[str] = mapped_column(Text)
    problem: Mapped[str] = mapped_column(Text)
    contribution: Mapped[str] = mapped_column(Text)
    methods: Mapped[str] = mapped_column(Text)
    outcome: Mapped[str | None] = mapped_column(Text, nullable=True)
    repository_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    live_demo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    skills: Mapped[list[Skill]] = relationship(
        secondary=project_skills,
        back_populates="projects",
    )
