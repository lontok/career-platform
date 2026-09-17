from datetime import date

from sqlalchemy import Boolean, Date, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Education(Base):
    __tablename__ = "education"
    __table_args__ = (
        Index("ux_education_seed_key", "seed_key", unique=True),
        Index("ix_education_published_display_order", "published", "display_order"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    seed_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    institution_name: Mapped[str] = mapped_column(String(255))
    degree_or_program: Mapped[str] = mapped_column(String(255))
    field_of_study: Mapped[str] = mapped_column(String(255))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    gpa: Mapped[str | None] = mapped_column(String(50), nullable=True)
    honors: Mapped[str | None] = mapped_column(Text, nullable=True)
    relevant_coursework: Mapped[str | None] = mapped_column(Text, nullable=True)
    certifications: Mapped[str | None] = mapped_column(Text, nullable=True)
    published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
