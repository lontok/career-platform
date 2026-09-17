from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(255))
    headline: Mapped[str] = mapped_column(String(255))
    summary: Mapped[str] = mapped_column(Text)
    location: Mapped[str] = mapped_column(String(255))
    target_roles: Mapped[str] = mapped_column(Text)
    email: Mapped[str] = mapped_column(String(320))
    linkedin_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    github_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    published: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, index=True
    )
