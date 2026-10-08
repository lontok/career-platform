from pydantic import field_validator
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
