import sqlite3

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import sessionmaker

from app.core.config import Settings


def register_sqlite_foreign_keys() -> None:
    if getattr(Engine, "_resume_sqlite_foreign_keys_registered", False):
        return

    @event.listens_for(Engine, "connect")
    def _enable_sqlite_foreign_keys(dbapi_connection, _) -> None:
        if not isinstance(dbapi_connection, sqlite3.Connection):
            return

        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Engine._resume_sqlite_foreign_keys_registered = True


register_sqlite_foreign_keys()

settings = Settings()
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

__all__ = ["SessionLocal", "engine", "register_sqlite_foreign_keys"]
