# Career Platform

A database-driven personal resume website for analytics and technical roles.

## Run locally in Codespaces

```bash
uv sync --all-groups
mkdir -p data
cp .env.example .env
uv run alembic upgrade head
uv run python -m app.seed
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Visit `/health` to confirm the application is running.

## Release verification

From a new Codespaces checkout, create the local database and run this exact
release checklist through the test suite:

```bash
uv sync --all-groups
mkdir -p data
uv run alembic upgrade head
uv run python -m app.seed
uv run ruff format --check .
uv run ruff check .
uv run pytest -q
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

With the server running, manually inspect `/`, `/experience`, `/projects`, a
valid project URL such as `/projects/career-platform`, `/skills`, `/education`,
`/health`, and an invalid project URL. Also perform a backup and restore drill
without using an existing target:

```bash
mkdir -p data/backup-verification
bash deploy/scripts/backup-sqlite.sh data/resume.db data/backup-verification
BACKUP_FILE="$(find data/backup-verification -type f -name '*.db' -print -quit)"
test -n "$BACKUP_FILE"
bash deploy/scripts/restore-sqlite.sh "$BACKUP_FILE" data/restored-resume.db
sqlite3 data/restored-resume.db "PRAGMA integrity_check;"
rm data/restored-resume.db
```

## Initialize the SQLite schema

```bash
mkdir -p data
cp .env.example .env
uv run alembic upgrade head
```

`DATABASE_URL` is loaded through `app.core.config.Settings`, so update `.env` when you want a different SQLite file location.

Do not commit SQLite database files. Keep local SQLite database files under `data/`; the repository ignores database files there (`*.db`, `*.db-wal`, `*.db-shm`, `*.db-journal`, plus matching `*.sqlite3` sidecar files). The `data/` directory itself is not globally ignored.

## Seed published resume content

```bash
uv run python -m app.seed
```

The seed command validates `app/fallback_profile.json` before writing and then inserts or updates representative published records for the profile, experience, project, skill, and education tables. Re-running it is safe and keeps the demo data idempotent.

## Update resume content safely

1. Back up the current SQLite file in `data/` before making content changes.
2. Edit the published seed content in `app/seed.py`; update `app/fallback_profile.json` only with intentionally public fallback profile data.
3. If the schema changes, create and apply a migration before seeding.
4. Run `uv run alembic upgrade head`.
5. Run `uv run python -m app.seed`.
6. Confirm the public resume pages render the updated published data once the page routes are available.

Ordinary resume content updates should stay in the database seed and fallback data files; they must not require template edits.

## Manual accessibility smoke checks

Before publishing a content update, confirm:

- Keyboard-only navigation reaches every navigation and content link.
- Keyboard focus remains visible on every interactive element.
- The mobile layout is readable without horizontal scrolling.
- Every page has one main heading.
- Links have descriptive text rather than bare URLs or ambiguous labels.
- Optional details never leave an empty label behind.

## Deployment

Use [`deploy/README.md`](deploy/README.md) for the complete Codespaces-to-Azure
VM runbook. It configures Uvicorn only on `127.0.0.1:8000`, with Nginx exposing
HTTPS publicly. Production SQLite data belongs at
`/var/lib/career-platform/resume.db`, outside the checkout, and the executable
backup and restore scripts validate integrity while refusing destructive
overwrites.