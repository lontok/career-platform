from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.skill import Skill


experience_skills = Table(
    "experience_skills",
    Base.metadata,
    Column(
        "experience_id",
        ForeignKey("experiences.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("skill_id", ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True),
)


class Experience(Base):
    __tablename__ = "experiences"
    __table_args__ = (
        Index("ux_experiences_seed_key", "seed_key", unique=True),
        Index(
            "ix_experiences_published_current_start_date",
            "published",
            "is_current",
            "start_date",
        ),
        Index("ix_experiences_published_display_order", "published", "display_order"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    seed_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role_title: Mapped[str] = mapped_column(String(255))
    organization: Mapped[str] = mapped_column(String(255))
    location: Mapped[str] = mapped_column(String(255))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    summary: Mapped[str] = mapped_column(Text)
    published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    accomplishments: Mapped[list[ExperienceAccomplishment]] = relationship(
        back_populates="experience",
        cascade="all, delete-orphan",
        order_by="ExperienceAccomplishment.display_order",
    )
    skills: Mapped[list[Skill]] = relationship(
        secondary=experience_skills,
        back_populates="experiences",
    )


class ExperienceAccomplishment(Base):
    __tablename__ = "experience_accomplishments"
    __table_args__ = (
        Index(
            "ix_experience_accomplishments_experience_display_order",
            "experience_id",
            "display_order",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    experience_id: Mapped[int] = mapped_column(
        ForeignKey("experiences.id", ondelete="CASCADE"),
        nullable=False,
    )
    statement: Mapped[str] = mapped_column(Text)
    metric: Mapped[str | None] = mapped_column(String(255), nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    experience: Mapped[Experience] = relationship(back_populates="accomplishments")
