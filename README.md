# Career Platform

A database-driven personal resume website for analytics and technical roles.

## Run locally in Codespaces

```bash
uv sync --all-groups
mkdir -p data
cp .env.example .env
uv run alembic upgrade head
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Visit `/health` to confirm the application is running.

## Initialize the SQLite schema

```bash
mkdir -p data
cp .env.example .env
uv run alembic upgrade head
```

`DATABASE_URL` is loaded through `app.core.config.Settings`, so update `.env` when you want a different SQLite file location.

Do not commit SQLite database files. Keep local SQLite database files under `data/`; the repository ignores database files there (`*.db`, `*.db-wal`, `*.db-shm`, `*.db-journal`, plus matching `*.sqlite3` sidecar files). The `data/` directory itself is not globally ignored.