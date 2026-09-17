from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.experience import Experience
    from app.models.project import Project


class Skill(Base):
    __tablename__ = "skills"
    __table_args__ = (
        Index(
            "ix_skills_published_category_display_order",
            "published",
            "category",
            "display_order",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    category: Mapped[str] = mapped_column(String(100), index=True)
    context: Mapped[str | None] = mapped_column(Text, nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    experiences: Mapped[list[Experience]] = relationship(
        secondary="experience_skills",
        back_populates="skills",
    )
    projects: Mapped[list[Project]] = relationship(
        secondary="project_skills",
        back_populates="skills",
    )
