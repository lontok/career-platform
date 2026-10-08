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
`/contact` (submit it once empty and once filled in),
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

The seed command validates `app/fallback_profile.json` before writing and then inserts or updates the site owner's published records for the profile, experience, project, skill, and education tables. Records removed from the seed data are unpublished, not deleted. Re-running it is safe and doesn't create duplicates. Tests use the fictional sample in `tests/seed_samples.py` instead.

Target roles are optional. Leave `target_roles` empty when the site shouldn't read as a job search, and the home page omits them.

Seeding refuses to write when the profile's headline, summary, or location is blank. The fallback profile follows the same rule. The home page leads with the headline and summary, so a blank one leaves the first screen empty.

Seeding also unpublishes every other profile and publishes the one in `app/seed.py`. If your database holds a profile you added another way, running the seed replaces it on the public site.

## Contact form

`/contact` shows a form with Name, Email, and Message. It posts to `/contact`, checks each field, and shows the sender what they submitted. Nothing is saved or emailed yet, and the confirmation page says so. Jinja escapes every value, so HTML typed into the form displays as plain text. Names can be up to 100 characters, email addresses up to 254, and messages up to 5000. The limits live in `app/services/contact.py`, and the form's `maxlength` attributes read from the same values.

## How the home page chooses what to show

The home page shows experiences marked `featured`. When none are featured, it shows the three most recent roles. The career timeline always shows every published role, and featured roles are drawn in a different color.

The executive summary lists up to four accomplishments that have a `metric`, in the same order as the experience list. Accomplishments without a metric still appear on `/experience`.

## Update resume content safely

1. Back up the current SQLite file in `data/` before making content changes.
2. Edit the published seed content in `app/seed.py`; update `app/fallback_profile.json` only with intentionally public fallback profile data.
3. If the schema changes, create and apply a migration before seeding. To highlight a role on the home page, set `featured` to true on that experience.
4. Run `uv run alembic upgrade head`.
5. Run `uv run python -m app.seed`.
6. Confirm the public resume pages render the updated published data once the page routes are available.

Ordinary resume content updates should stay in the database seed and fallback data files; they must not require template edits.

Avoid `op.batch_alter_table` in migrations for any table that other tables point to, such as `experiences`, `skills`, or `projects`. On SQLite, batch mode rebuilds the table by dropping the old one. Migrations run with foreign keys on, so that drop deletes every linked row in tables declared `ON DELETE CASCADE`, such as accomplishments and skill links. Use `op.add_column`, which changes the table in place. `tests/test_migrations.py` upgrades a database that holds linked rows and fails if any go missing.

## Manual accessibility smoke checks

Before publishing a content update, confirm:

- Keyboard-only navigation reaches every navigation and content link.
- Keyboard focus remains visible on every interactive element.
- The mobile layout is readable without horizontal scrolling.
- Every page has one main heading.
- Links have descriptive text rather than bare URLs or ambiguous labels.
- Optional details never leave an empty label behind.

## Deployment

The site runs on Railway with PostgreSQL. [`deploy/railway.md`](deploy/railway.md)
covers what runs on each deploy and the one variable the service needs. Don't
run the seed against the Railway database.

The Azure VM runbook in [`deploy/README.md`](deploy/README.md) still describes
the SQLite setup on the VM. Once `lontok.xyz` points at Railway, the VM stays
up as a fallback until it's retired.

To run the Postgres tests, start a local Postgres 18 container and set
`TEST_POSTGRES_URL` to it. Without that variable, those tests skip.
