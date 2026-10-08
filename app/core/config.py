import os

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

POSTGRES_PREFIXES = ("postgres://", "postgresql://")


class Settings(BaseSettings):
    database_url: str = "sqlite:///./data/resume.db"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Railway hands out postgresql:// URLs, which SQLAlchemy maps to psycopg2.
    # This app installs psycopg 3, so name that driver explicitly.
    @field_validator("database_url")
    @classmethod
    def use_psycopg_driver(cls, value: str) -> str:
        for prefix in POSTGRES_PREFIXES:
            if value.startswith(prefix):
                return "postgresql+psycopg://" + value.removeprefix(prefix)
        return value

    # Without DATABASE_URL, Railway would quietly fall back to a throwaway
    # SQLite file while /health stays green. Stop the deploy instead.
    @model_validator(mode="after")
    def require_postgres_on_railway(self) -> "Settings":
        on_railway = bool(os.environ.get("RAILWAY_ENVIRONMENT_ID"))
        if on_railway and not self.database_url.startswith("postgresql+psycopg://"):
            raise ValueError("DATABASE_URL must point at Postgres on Railway")
        return self
