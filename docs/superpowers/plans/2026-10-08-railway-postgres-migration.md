# Railway and PostgreSQL migration implementation plan

> For agentic workers: REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

This is a first draft and is open to revisions. A dated result line goes under each step as it runs. Nothing has run yet.

## What's there now

These details came from read-only checks on 2026-10-08.

| Item | Value |
| --- | --- |
| Railway project | `career-platform-rehearsal`, one environment, `production` |
| Web service | `career-platform-rehearsal`, built by Railpack from the repo `lontok/career-platform-rehearsal`, last deploy `SUCCESS` |
| Web service domains | `greglontok.com`, `www.greglontok.com`, and `career-platform-rehearsal-production.up.railway.app` |
| Web service settings | No start command, pre-deploy command, or health check path set |
| Postgres service | `Postgres`, PostgreSQL 18.6, no tables in the `public` schema |
| Postgres from the laptop | `RAILWAY_DATABASE_URL` in `.env`, the public proxy URL |
| VM database | `/home/azureuser/career-platform/data/resume.db`, Alembic revision `20261006_04` |
| VM row counts | education 3, experience_accomplishments 1, experience_skills 2, experiences 8, profiles 1, project_skills 0, projects 1, skills 6 |
| VM web server | Nginx with a Certbot certificate for `lontok.xyz` and `www.lontok.xyz`. HTTP redirects to HTTPS, and the bare IP returns `404`. |
| `lontok.xyz` DNS | Registered at Namecheap, with nameservers at Cloudflare. `lontok.xyz` and `www.lontok.xyz` are A records for `20.112.93.148`, not proxied. |

Today the VM serves `lontok.xyz`, and the rehearsal service on Railway serves `greglontok.com`. This plan points the existing web service at this repo, then moves `lontok.xyz` from the VM to that service.

## Goal and approach

Goal: `https://lontok.xyz` is served by the existing Railway web service, which runs `lontok/career-platform` from `main` against the Railway Postgres, with the same content the VM shows today.

The app has only ever run on SQLite. Four things stop it from running on Postgres or behind Railway as it stands:

1. It has no Postgres driver. Railway's `DATABASE_URL` starts with `postgresql://`, which SQLAlchemy maps to `psycopg2`, and that isn't installed.
2. Migration `20260917_02` compares a boolean column to `1` and `0`. SQLite accepts that, but Postgres stops with `operator does not exist: boolean = integer`, so `alembic upgrade head` fails on an empty database.
3. The index that allows only one published profile is partial on SQLite only (`sqlite_where`). On Postgres it becomes a plain unique index on `published`, so a second unpublished profile would also be rejected.
4. The templates build absolute URLs for the stylesheet and navigation. Railway serves the site over HTTPS but talks to Uvicorn over HTTP. Uvicorn ignores Railway's `X-Forwarded-Proto` header by default, so the page would link `http://` CSS from an `https://` page and the browser would block it.

The data moves by copying every row from the VM's SQLite file, which you chose over reseeding. That keeps the published `career-platform` project and the unpublished sample rows. A new script, `app/copy_sqlite.py`, copies the rows into a migrated, empty Postgres and resets the ID sequences so new rows don't collide.

Copying instead of seeding has one consequence. `python -m app.seed` must not run on Railway. `SEED_PROJECTS` is empty, so the seed would unpublish the copied project. The pre-deploy command only runs migrations, and a test pins that.

The order keeps `lontok.xyz` up the whole time. Postgres gets its schema and data from the laptop first, so the first deploy of this app finds a full database instead of showing the fallback profile. Then the source repo switches, and the Railway copy gets checked page by page against the VM through its `up.railway.app` address. Only after that do the DNS records for `lontok.xyz` move from the VM to Railway. Until DNS moves, visitors keep reaching the VM.

Railway settings live in a committed `railway.json`, not the CLI. Dashboard steps are written for Greg to click through.

Tech stack: FastAPI, SQLAlchemy 2, Alembic, psycopg 3, Uvicorn, uv, Railpack on Railway, and PostgreSQL 18. Tests run on SQLite as before, plus a Postgres suite against a local Docker container.

Spec: Greg's request in chat on 2026-10-08 and his answers to two questions, which have no separate file. Railway runs this repo in the existing service, and the data comes from copying the SQLite rows.

## Global constraints

- Don't run the `railway` CLI. Use `railway.json` and the dashboard.
- Never run `python -m app.seed` against the Railway Postgres, from the laptop or from a Railway command.
- Don't change, pull, or commit any file in the VM's checkout. The VM keeps serving `lontok.xyz` until Greg decides otherwise.
- Don't add an HTTPS redirect to the app. Railway's edge handles HTTPS for `lontok.xyz` on its own, as Certbot and Nginx do on the VM today.
- Leave the VM running and its Nginx and Certbot setup alone. After DNS moves, it's the fallback.
- Keep SQLite working. Local runs and the default test suite stay on SQLite, and the existing tests must still pass.
- Postgres tests only run against a local throwaway database. The fixture drops the `public` schema, so it refuses any host other than `localhost` or `127.0.0.1`.
- Never print a database URL with its password. Use the `.env` value through a variable, and check URLs with the password cut out.
- Use the project's uv virtual environment for everything. `uv add` updates `uv.lock`, and Railpack builds with the lock.
- "Laptop" means a terminal in this repo. "VM" means a terminal after SSH into the VM. "Dashboard" means the Railway dashboard in a browser.

## Review focus

These are the five conditions most likely to break the move, each with the test or step that checks it.

1. The database password contains `%`. Alembic's `env.py` passes the URL through `configparser`, which reads `%` as interpolation and rejects the URL. Task 2 escapes it, and the Postgres suite runs with a password containing `%`.
2. The SQLite file sits under a path with spaces, like this repo's `My Drive` folder. A hand-built `sqlite:///file:...?mode=ro` URL breaks on spaces. Task 3 opens the file through `Path.as_uri()`, and its test uses a folder name with a space.
3. The copy runs twice, or against the wrong database. A second run would duplicate rows or fail halfway. Task 3 refuses a target with any rows and refuses mismatched Alembic revisions, all inside one transaction.
4. New rows after the copy collide with copied IDs, because Postgres sequences still start at 1. Task 3 resets every sequence, and its test inserts a row without an ID after copying.
5. The site renders unstyled on `https://lontok.xyz` because of `http://` asset links. Task 4 adds `--forwarded-allow-ips "*"` to the start command, and a test pins it. Steps 5.6 and 5.9 check the live stylesheet link.

---

### Task 1: Postgres driver and URL handling

Files:

- Modify: `pyproject.toml`, `uv.lock` (through `uv add`)
- Modify: `app/core/config.py`
- Create: `tests/test_config.py`

Interfaces:

- Produces: `Settings().database_url` always uses the `postgresql+psycopg://` driver for Postgres URLs and leaves SQLite URLs alone. Tasks 2 and 3 rely on this.

- [ ] Step 1.1: Write the failing test.

`tests/test_config.py`:

```python
import pytest

from app.core.config import Settings


@pytest.mark.parametrize(
    "raw_url",
    ["postgres://user:secret@db.internal:5432/railway", "postgresql://user:secret@db.internal:5432/railway"],
)
def test_postgres_urls_use_the_psycopg_driver(raw_url: str) -> None:
    settings = Settings(database_url=raw_url)

    assert settings.database_url == "postgresql+psycopg://user:secret@db.internal:5432/railway"


@pytest.mark.parametrize(
    "url",
    [
        "postgresql+psycopg://user:secret@db.internal:5432/railway",
        "sqlite:///./data/resume.db",
        "sqlite+pysqlite:////tmp/resume-test.db",
    ],
)
def test_other_urls_are_unchanged(url: str) -> None:
    assert Settings(database_url=url).database_url == url
```

- [ ] Step 1.2: Run it and confirm it fails.

Run: `uv run pytest tests/test_config.py -v`
Expected: the two `test_postgres_urls_use_the_psycopg_driver` cases FAIL because the URL comes back unchanged. The three unchanged-URL cases pass.

- [ ] Step 1.3: Add the driver.

Run: `uv add "psycopg[binary]>=3.2"`
Check: `pyproject.toml` lists `psycopg[binary]` under `dependencies`, and `uv.lock` changed.

- [ ] Step 1.4: Normalize the URL in `app/core/config.py`.

```python
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
```

- [ ] Step 1.5: Run the tests and confirm they pass.

Run: `uv run pytest tests/test_config.py -v && uv run pytest -q && uv run ruff check .`
Expected: all PASS, and ruff reports no errors.

- [ ] Step 1.6: Commit.

```bash
git add pyproject.toml uv.lock app/core/config.py tests/test_config.py
git commit -m "feat: connect to Postgres through psycopg"
```

---

### Task 2: Migrations and models that run on Postgres

Files:

- Modify: `alembic/versions/20260917_02_add_seed_keys.py:61-85`
- Modify: `app/models/profile.py:11-16`
- Modify: `alembic/env.py:17`
- Create: `tests/postgres_support.py`
- Create: `tests/test_postgres.py`

Interfaces:

- Consumes: `Settings` from Task 1.
- Produces: `tests/postgres_support.py` with `POSTGRES_URL: str | None`, `requires_postgres` (a `pytest.mark.skipif` marker), `alembic_config() -> alembic.config.Config`, and the fixture `postgres_url(monkeypatch) -> str`, which empties the database and sets `DATABASE_URL` to it. Task 3's tests import these.

Editing migration `20260917_02` is safe here. The VM's SQLite already ran it and never runs it again, and the SQLite behavior doesn't change: `true` and `false` are `1` and `0` in SQLite 3.23 and later. The only database that will run the new text is the empty Railway Postgres.

- [ ] Step 2.1: Start a throwaway Postgres 18 on the laptop.

```bash
docker run -d --name career-platform-pg-test -e POSTGRES_PASSWORD='te%st' -p 55432:5432 postgres:18
export TEST_POSTGRES_URL='postgresql://postgres:te%25st@localhost:55432/postgres'
```

The password has a `%` on purpose (Review focus 1). In a URL it's written `%25`.
Check: `docker ps --filter name=career-platform-pg-test` shows the container as `Up`.
Undo: `docker rm -f career-platform-pg-test`.

- [ ] Step 2.2: Write the shared Postgres test helpers.

`tests/postgres_support.py`:

```python
from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import urlsplit

import pytest
from alembic.config import Config
from sqlalchemy import create_engine, text

from app.core.config import Settings

REPO_ROOT = Path(__file__).resolve().parent.parent
POSTGRES_URL = os.environ.get("TEST_POSTGRES_URL")
LOCAL_HOSTS = {"localhost", "127.0.0.1"}

requires_postgres = pytest.mark.skipif(
    not POSTGRES_URL, reason="TEST_POSTGRES_URL is not set"
)


def alembic_config() -> Config:
    config = Config(str(REPO_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(REPO_ROOT / "alembic"))
    return config


@pytest.fixture
def postgres_url(monkeypatch) -> str:
    if urlsplit(POSTGRES_URL).hostname not in LOCAL_HOSTS:
        pytest.fail("TEST_POSTGRES_URL must point at a local throwaway database")

    engine = create_engine(Settings(database_url=POSTGRES_URL).database_url)
    with engine.begin() as connection:
        connection.execute(text("DROP SCHEMA public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))
    engine.dispose()

    monkeypatch.setenv("DATABASE_URL", POSTGRES_URL)
    return POSTGRES_URL
```

- [ ] Step 2.3: Write the failing Postgres tests.

`tests/test_postgres.py`:

```python
from __future__ import annotations

import pytest
from alembic import command
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError

from app.core.config import Settings
from app.db.session import create_session_factory
from app.seed import seed_demo_content
from tests.postgres_support import alembic_config, postgres_url, requires_postgres

pytestmark = requires_postgres
__all__ = ["postgres_url"]

INSERT_PROFILE = text(
    "INSERT INTO profiles (full_name, headline, summary, location, target_roles,"
    " email, published) VALUES (:name, 'Headline', 'Summary', 'Los Angeles', '',"
    " '', :published)"
)


def _engine(url: str):
    return create_engine(Settings(database_url=url).database_url)


def test_upgrade_head_builds_the_schema(postgres_url: str) -> None:
    command.upgrade(alembic_config(), "head")

    engine = _engine(postgres_url)
    with engine.connect() as connection:
        version = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
    tables = set(inspect(engine).get_table_names())
    engine.dispose()

    assert version == "20261006_04"
    assert {"profiles", "skills", "experiences", "experience_accomplishments",
            "experience_skills", "projects", "project_skills", "education"} <= tables


def test_many_profiles_can_be_unpublished_but_only_one_published(postgres_url: str) -> None:
    command.upgrade(alembic_config(), "head")
    engine = _engine(postgres_url)

    with engine.begin() as connection:
        connection.execute(INSERT_PROFILE, {"name": "Draft One", "published": False})
        connection.execute(INSERT_PROFILE, {"name": "Draft Two", "published": False})
        connection.execute(INSERT_PROFILE, {"name": "Live One", "published": True})

    with pytest.raises(IntegrityError):
        with engine.begin() as connection:
            connection.execute(INSERT_PROFILE, {"name": "Live Two", "published": True})
    engine.dispose()


def test_seed_runs_against_postgres(postgres_url: str, sample_seed) -> None:
    command.upgrade(alembic_config(), "head")
    engine, session_factory = create_session_factory(Settings().database_url)

    seed_demo_content(session_factory=session_factory)
    seed_demo_content(session_factory=session_factory)

    with engine.connect() as connection:
        published = connection.execute(
            text("SELECT count(*) FROM profiles WHERE published")
        ).scalar_one()
    engine.dispose()
    assert published == 1
```

The seed runs twice to prove the upserts are repeatable on Postgres. This is a local test database, so the rule against seeding Railway doesn't apply.

- [ ] Step 2.4: Run the Postgres tests and confirm they fail.

Run: `uv run pytest tests/test_postgres.py -v`
Expected: every test FAILS during `command.upgrade`. With the `%` password the first error comes from `configparser`, which calls the URL invalid interpolation syntax. Once that's fixed in Step 2.5, the next is `psycopg.errors.UndefinedFunction: operator does not exist: boolean = integer`.

- [ ] Step 2.5: Escape `%` in `alembic/env.py`.

Replace line 17:

```python
# configparser treats % as interpolation, and URL-encoded passwords contain it.
config.set_main_option("sqlalchemy.url", settings.database_url.replace("%", "%%"))
```

- [ ] Step 2.6: Use boolean literals and a Postgres partial index in migration `20260917_02`.

Replace the `UPDATE profiles SET published = 0` block and the `ux_profiles_single_published` index with:

```python
    op.execute(
        """
        UPDATE profiles
        SET published = false
        WHERE published = true
          AND id != (
              SELECT id
              FROM profiles
              WHERE published = true
              ORDER BY
                  CASE WHEN seed_key = 'profile:primary' THEN 0 ELSE 1 END,
                  id
              LIMIT 1
          )
        """
    )

    op.create_index("ux_profiles_seed_key", "profiles", ["seed_key"], unique=True)
    op.create_index(
        "ux_profiles_single_published",
        "profiles",
        ["published"],
        unique=True,
        sqlite_where=sa.text("published = 1"),
        postgresql_where=sa.text("published"),
    )
```

- [ ] Step 2.7: Match the model in `app/models/profile.py`.

```python
        Index(
            "ux_profiles_single_published",
            "published",
            unique=True,
            sqlite_where=text("published = 1"),
            postgresql_where=text("published"),
        ),
```

- [ ] Step 2.8: Run every test and confirm they pass.

Run: `uv run pytest tests/test_postgres.py -v && uv run pytest -q && uv run ruff check .`
Expected: the three Postgres tests PASS. The full suite passes, including `tests/test_migrations.py` on SQLite. Without `TEST_POSTGRES_URL` set, the Postgres tests show as skipped.

- [ ] Step 2.9: Commit.

```bash
git add alembic/env.py alembic/versions/20260917_02_add_seed_keys.py app/models/profile.py tests/postgres_support.py tests/test_postgres.py
git commit -m "fix: run the migrations on Postgres"
```

---

### Task 3: Copy the SQLite rows into Postgres

Files:

- Create: `app/copy_sqlite.py`
- Create: `tests/test_copy_sqlite.py`

Interfaces:

- Consumes: `Settings` (Task 1), `tests/postgres_support.py` (Task 2), `Base.metadata` from `app/db/base.py` with every model imported through `app.models`.
- Produces: `copy_database(source: Engine, target: Engine) -> dict[str, int]`, which returns rows copied per table, and `main(argv: list[str] | None = None) -> None`. Run it as `uv run python -m app.copy_sqlite <path-to-sqlite-file>` with `DATABASE_URL` set to the Postgres target.

- [ ] Step 3.1: Write the failing tests.

`tests/test_copy_sqlite.py`:

```python
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from alembic import command
from sqlalchemy import create_engine, text

from app.copy_sqlite import copy_database, main, open_sqlite_read_only
from app.core.config import Settings
from app.db.session import create_session_factory
from app.seed import seed_demo_content
from tests.postgres_support import alembic_config, postgres_url, requires_postgres

__all__ = ["postgres_url"]

COPIED_TABLES = ("profiles", "skills", "experiences", "experience_accomplishments",
                 "experience_skills", "projects", "project_skills", "education")


def _build_source(monkeypatch, folder: Path, revision: str = "head") -> Path:
    # The space in the folder name matches this repo's "My Drive" path.
    folder.mkdir()
    database = folder / "resume.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database}")
    command.upgrade(alembic_config(), revision)
    return database


def _counts(engine) -> dict[str, int]:
    with engine.connect() as connection:
        return {
            table: connection.execute(text(f"SELECT count(*) FROM {table}")).scalar_one()
            for table in COPIED_TABLES
        }


def test_main_refuses_a_missing_file(tmp_path: Path) -> None:
    with pytest.raises(SystemExit, match="No SQLite file"):
        main([str(tmp_path / "missing.db")])


def test_main_refuses_a_sqlite_target(monkeypatch, tmp_path: Path) -> None:
    source = tmp_path / "resume.db"
    sqlite3.connect(source).close()
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'target.db'}")

    with pytest.raises(SystemExit, match="must point at Postgres"):
        main([str(source)])


@requires_postgres
def test_copy_matches_every_table_and_resets_sequences(
    monkeypatch, tmp_path: Path, postgres_url: str, sample_seed
) -> None:
    source_path = _build_source(monkeypatch, tmp_path / "My Drive")
    seed_demo_content(session_factory=create_session_factory(f"sqlite:///{source_path}")[1])
    monkeypatch.setenv("DATABASE_URL", postgres_url)
    command.upgrade(alembic_config(), "head")

    source = open_sqlite_read_only(source_path)
    target = create_engine(Settings().database_url)
    copied = copy_database(source, target)

    assert copied == _counts(source)
    assert _counts(target) == _counts(source)
    with target.begin() as connection:
        largest = connection.execute(text("SELECT max(id) FROM skills")).scalar_one()
        new_id = connection.execute(
            text("INSERT INTO skills (name, category, published, display_order)"
                 " VALUES ('Added Later', 'misc', false, 99) RETURNING id")
        ).scalar_one()
    source.dispose()
    target.dispose()
    assert new_id > largest


@requires_postgres
def test_copy_refuses_a_target_that_has_rows(
    monkeypatch, tmp_path: Path, postgres_url: str, sample_seed
) -> None:
    source_path = _build_source(monkeypatch, tmp_path / "source db")
    seed_demo_content(session_factory=create_session_factory(f"sqlite:///{source_path}")[1])
    monkeypatch.setenv("DATABASE_URL", postgres_url)
    command.upgrade(alembic_config(), "head")
    source = open_sqlite_read_only(source_path)
    target = create_engine(Settings().database_url)
    copy_database(source, target)

    with pytest.raises(ValueError, match="is not empty"):
        copy_database(source, target)
    counts_after = _counts(target)
    source.dispose()
    target.dispose()
    assert counts_after == _counts(open_sqlite_read_only(source_path))


@requires_postgres
def test_copy_refuses_mismatched_revisions(
    monkeypatch, tmp_path: Path, postgres_url: str
) -> None:
    source_path = _build_source(monkeypatch, tmp_path / "old db", revision="20261006_03")
    monkeypatch.setenv("DATABASE_URL", postgres_url)
    command.upgrade(alembic_config(), "head")
    source = open_sqlite_read_only(source_path)
    target = create_engine(Settings().database_url)

    with pytest.raises(ValueError, match="20261006_03"):
        copy_database(source, target)
    source.dispose()
    target.dispose()
```

- [ ] Step 3.2: Run them and confirm they fail.

Run: `uv run pytest tests/test_copy_sqlite.py -v`
Expected: collection fails with `ModuleNotFoundError: No module named 'app.copy_sqlite'`.

- [ ] Step 3.3: Write `app/copy_sqlite.py`.

```python
"""Copy every resume row from a SQLite file into an empty, migrated Postgres.

Usage: DATABASE_URL=<postgres url> uv run python -m app.copy_sqlite <sqlite file>
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

from sqlalchemy import Engine, create_engine, func, select, text

from app import models  # noqa: F401
from app.core.config import Settings
from app.db.base import Base


def open_sqlite_read_only(path: Path) -> Engine:
    # as_uri() percent-encodes spaces, which a hand-built sqlite URL would not.
    uri = f"{Path(path).resolve().as_uri()}?mode=ro"
    return create_engine("sqlite://", creator=lambda: sqlite3.connect(uri, uri=True))


def copy_database(source: Engine, target: Engine) -> dict[str, int]:
    source_version = _alembic_version(source)
    target_version = _alembic_version(target)
    if source_version != target_version:
        raise ValueError(
            f"Source is at {source_version} but target is at {target_version}"
        )

    tables = Base.metadata.sorted_tables
    copied: dict[str, int] = {}
    with source.connect() as reader, target.begin() as writer:
        for table in tables:
            if writer.scalar(select(func.count()).select_from(table)):
                raise ValueError(f"Target table {table.name} is not empty")

        for table in tables:
            rows = [dict(row._mapping) for row in reader.execute(select(table))]
            if rows:
                writer.execute(table.insert(), rows)
            copied[table.name] = len(rows)

        # Rows arrive with their SQLite IDs, so move each sequence past them.
        for table in tables:
            if "id" in table.c and table.c.id.primary_key:
                writer.execute(
                    text(
                        f"SELECT setval(pg_get_serial_sequence('{table.name}', 'id'),"
                        f" COALESCE((SELECT max(id) FROM {table.name}), 1),"
                        f" (SELECT max(id) FROM {table.name}) IS NOT NULL)"
                    )
                )
    return copied


def main(argv: list[str] | None = None) -> None:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        raise SystemExit("Usage: python -m app.copy_sqlite <sqlite file>")

    source_path = Path(args[0])
    if not source_path.is_file():
        raise SystemExit(f"No SQLite file at {source_path}")

    target_url = Settings().database_url
    if not target_url.startswith("postgresql+psycopg://"):
        raise SystemExit("DATABASE_URL must point at Postgres")

    source = open_sqlite_read_only(source_path)
    target = create_engine(target_url)
    try:
        copied = copy_database(source, target)
    finally:
        source.dispose()
        target.dispose()

    for table_name, count in copied.items():
        print(f"{table_name}: {count}")


def _alembic_version(engine: Engine) -> str:
    with engine.connect() as connection:
        return connection.execute(
            text("SELECT version_num FROM alembic_version")
        ).scalar_one()


if __name__ == "__main__":
    main()
```

- [ ] Step 3.4: Run every test and confirm they pass.

Run: `uv run pytest tests/test_copy_sqlite.py -v && uv run pytest -q && uv run ruff check .`
Expected: all five copy tests PASS with `TEST_POSTGRES_URL` set. Without it, the two `main` tests pass and the three Postgres tests skip.

- [ ] Step 3.5: Commit.

```bash
git add app/copy_sqlite.py tests/test_copy_sqlite.py
git commit -m "feat: add a one-time SQLite to Postgres copy"
```

---

### Task 4: Railway config and docs

Files:

- Create: `railway.json`
- Modify: `tests/test_deploy_assets.py` (add one test at the end)
- Create: `deploy/railway.md`
- Modify: `README.md`, the `## Deployment` section

Interfaces:

- Consumes: `alembic upgrade head` from Task 2 and `/health` from `app/main.py`.
- Produces: the settings Railway reads from the repo on every deploy. Section 5 relies on them.

- [ ] Step 4.1: Write the failing test.

Add to the end of `tests/test_deploy_assets.py`, and add `import json` to its imports:

```python
def test_railway_migrates_without_seeding_and_trusts_its_proxy() -> None:
    deploy = json.loads(Path("railway.json").read_text())["deploy"]

    assert deploy["preDeployCommand"] == "alembic upgrade head"
    assert "app.seed" not in json.dumps(deploy)
    assert "--host 0.0.0.0" in deploy["startCommand"]
    assert "--port $PORT" in deploy["startCommand"]
    assert '--forwarded-allow-ips "*"' in deploy["startCommand"]
    assert deploy["healthcheckPath"] == "/health"
```

- [ ] Step 4.2: Run it and confirm it fails.

Run: `uv run pytest tests/test_deploy_assets.py -v`
Expected: the new test FAILS with `FileNotFoundError: railway.json`.

- [ ] Step 4.3: Write `railway.json`.

```json
{
  "$schema": "https://railway.com/railway.schema.json",
  "build": {
    "builder": "RAILPACK"
  },
  "deploy": {
    "preDeployCommand": "alembic upgrade head",
    "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT --forwarded-allow-ips \"*\"",
    "healthcheckPath": "/health",
    "restartPolicyType": "ON_FAILURE"
  }
}
```

Railway's docs confirm that `$PORT` expands in the start command and that the pre-deploy command can reach service variables and the private network. Uvicorn already reads proxy headers. `--forwarded-allow-ips "*"` makes it trust them from Railway's edge, which isn't on `127.0.0.1`.

- [ ] Step 4.4: Run the tests and confirm they pass.

Run: `uv run pytest -q && uv run ruff check .`
Expected: all PASS.

- [ ] Step 4.5: Write `deploy/railway.md`.

```markdown
# Railway deployment

The web service in the Railway project `career-platform-rehearsal` builds this
repo from `main` with Railpack and serves `lontok.xyz`. `railway.json` holds its settings, so a change
there ships with the next push. Settings in the dashboard are overridden by it.

## What runs on each deploy

1. Railpack installs the locked dependencies from `uv.lock`.
2. The pre-deploy command runs `alembic upgrade head` against the Railway
   Postgres. A failed migration stops the deploy, and the old one keeps serving.
3. Uvicorn starts on `$PORT` and trusts Railway's forwarded headers, so links on
   the page use `https://`.
4. Railway sends traffic to the new deploy once `/health` answers.

## Domain

`lontok.xyz` and `www.lontok.xyz` are custom domains on the web service. Their
DNS lives at Cloudflare as CNAME records to the target Railway shows, set to DNS
only, plus Railway's TXT verification record. Railway issues the certificate.

## Variables

The web service needs one variable, `DATABASE_URL`, set to the reference
`${{Postgres.DATABASE_URL}}`. That URL uses Railway's private network.

## Rules

- Never run `python -m app.seed` against the Railway Postgres. The data was
  copied from the VM's SQLite on 2026-10-08, and the seed would unpublish the
  `career-platform` project, since `SEED_PROJECTS` is empty.
- Content changes go through a migration, like `20261006_04`, so they run in the
  pre-deploy step.
- `app/copy_sqlite.py` was for the one-time move. It refuses a database that
  already has rows.
```

- [ ] Step 4.6: Update `README.md`.

Replace the `## Deployment` section with:

```markdown
## Deployment

The site runs on Railway with PostgreSQL. [`deploy/railway.md`](deploy/railway.md)
covers what runs on each deploy and the one variable the service needs. Don't
run the seed against the Railway database.

The Azure VM runbook in [`deploy/README.md`](deploy/README.md) still describes
the SQLite setup on the VM. The VM stopped serving `lontok.xyz` on the day of
the move and stays up as a fallback until it's retired.

To run the Postgres tests, start a local Postgres 18 container and set
`TEST_POSTGRES_URL` to it. Without that variable, those tests skip.
```

Check: `uv run pytest tests/test_deploy_assets.py -q` still passes, since `test_readme_lists_release_quality_commands` reads the README.

- [ ] Step 4.7: Commit.

```bash
git add railway.json tests/test_deploy_assets.py deploy/railway.md README.md
git commit -m "feat: deploy to Railway with Postgres"
```

---

## 5. Move the data and switch the service

These steps change live systems, so each one waits for Greg's go-ahead. Tasks 1 through 4 must be merged to `main` and pushed first. Pushing to `main` deploys nothing, because the Railway service still builds the rehearsal repo and the VM doesn't pull on its own.

- [x] Step 5.1: Take a fresh copy of the VM database.
  - Runs on: VM, then laptop.
  - Do:

    ```bash
    # VM
    cd ~/career-platform && ./deploy/scripts/backup-sqlite.sh data/resume.db data/backups
    # Laptop, with the path the VM printed
    scp -i ~/.ssh/isba4775_azure azureuser@20.112.93.148:<printed backup path> data/vm-resume-2026-10-08.db
    ```

  - Why: The backup script copies the file safely while the app is running and checks its integrity. The VM's `data/backups` folder is ignored by git, so the checkout stays clean.
  - Check: `sqlite3 data/vm-resume-2026-10-08.db "PRAGMA integrity_check; SELECT version_num FROM alembic_version;"` prints `ok` and `20261006_04`. Row counts match the table at the top.
  - Undo: delete `data/vm-resume-2026-10-08.db` on the laptop and the backup file on the VM.
  - Result, 2026-10-08 (VM half only): the script wrote `data/backups/resume-20261008T214826Z-18531.db`, 131,072 bytes with mode `600`. Read back on the VM, it passed `PRAGMA integrity_check` with `ok` and is at revision `20261006_04`. Every table's row count matched the live database and the table at the top. The published profile is `Greg Lontok`, and the published project is `career-platform`. `git status` in the VM checkout stayed clean.
  - Result, 2026-10-08 (laptop half): `scp -p` copied the backup to `data/vm-resume-2026-10-08.db`, set to mode `600`. Its SHA-256 matched the VM file (`20f8522b…557bc2`). Read on the laptop, it passed `integrity_check`, is at `20261006_04`, and has the same row counts. Git ignores it through `data/*.db`. The repo sits in Google Drive, so this file syncs to Drive like the rest of the folder.

- [ ] Step 5.2: Build the schema in the Railway Postgres from the laptop.
  - Runs on: laptop.
  - Do:

    ```bash
    export DATABASE_URL="$(grep '^RAILWAY_DATABASE_URL=' .env | cut -d= -f2- | tr -d '"')"
    uv run alembic upgrade head
    ```

  - Why: The schema and data go in before the service switches, so the first deploy of this app finds a full database. The pre-deploy migration then has nothing to do.
  - Check: before running Alembic, `echo "$DATABASE_URL" | sed -E 's#//[^@]*@#//#'` shows the same host and port as `DATABASE_PUBLIC_URL` on the Postgres service's Variables tab. The `.env` value is the only link to this project, so confirm it isn't another project's database. After running it, `psql "$DATABASE_URL" -Atc "SELECT version_num FROM alembic_version"` prints `20261006_04`.
  - Undo: `psql "$DATABASE_URL" -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"`. The database was empty before this step, but confirm with Greg before running it.

- [ ] Step 5.3: Copy the rows.
  - Runs on: laptop, in the same shell as 5.2.
  - Do: `uv run python -m app.copy_sqlite data/vm-resume-2026-10-08.db`
  - Why: This is the move itself. The script refuses to run if 5.2 didn't finish or if anything is already there.
  - Check: the printed counts match the table at the top. `psql "$DATABASE_URL" -Atc "SELECT full_name FROM profiles WHERE published"` prints `Greg Lontok`, and `SELECT slug FROM projects WHERE published` prints `career-platform`.
  - Undo: the same as 5.2, then rerun 5.2 and 5.3.

- [ ] Step 5.4: Point the web service at the Railway Postgres.
  - Runs on: dashboard.
  - Do: open the `career-platform-rehearsal` service, then Variables. If a `DATABASE_URL` exists, note its current value and replace it. Otherwise add one. Set it to `${{Postgres.DATABASE_URL}}`. Don't deploy the staged change yet.
  - Why: The reference uses the private network and follows the Postgres password if it changes.
  - Check: the variable shows as a reference to `Postgres`.
  - Undo: restore the old value, or remove the variable.

- [ ] Step 5.5: Switch the source repo.
  - Runs on: dashboard.
  - Do: in the service's Settings, under Source, disconnect `lontok/career-platform-rehearsal` and connect `lontok/career-platform` on branch `main`. Then deploy the staged changes.
  - Why: This puts this app on the service. `lontok.xyz` still points at the VM, so visitors don't see it yet. The service's other domains, `greglontok.com` and `www.greglontok.com`, serve this app from here on. Railway keeps the old deploy serving until the new one passes `/health`.
  - Check: in Deployments, the new deploy's build log shows Railpack running `uv sync`. The pre-deploy log shows Alembic finding nothing to upgrade, and the deploy ends `SUCCESS`. If it fails with `uvicorn: not found` or `alembic: not found`, change both commands in `railway.json` to start with `.venv/bin/`, push, and record that here.
  - Undo: switch Source back to `lontok/career-platform-rehearsal`. The rehearsal repo has no `railway.json`, so its old dashboard settings apply again.

- [ ] Step 5.6: Compare the Railway site with the VM.
  - Runs on: laptop.
  - Do:

    ```bash
    for path in / /experience /projects /projects/career-platform /skills /education /contact /health; do
      a=$(curl -s "https://lontok.xyz$path" | sed -E 's#https?://[^/"]+##g' | shasum)
      b=$(curl -s "https://career-platform-rehearsal-production.up.railway.app$path" | sed -E 's#https?://[^/"]+##g' | shasum)
      echo "$path $([ "$a" = "$b" ] && echo same || echo DIFFERENT)"
    done
    curl -s https://career-platform-rehearsal-production.up.railway.app/ | grep -o '<link rel="stylesheet" href="[^"]*"'
    ```

  - Why: `lontok.xyz` still points at the VM here, so it's the baseline. The bare IP can't be, since Nginx answers it with `404`. The `sed` strips the host from absolute links, so any difference left is content. The last line checks Review focus 5.
  - Check: every path prints `same`. The stylesheet link starts with `https://career-platform-rehearsal-production.up.railway.app/static/`. The VM runs `9432a93`, one commit behind `main`, but that commit changed only a migration, a test, and the README, so pages should match. If a page differs, diff the two bodies before going further.
  - Undo: none needed, since this step only reads.

- [ ] Step 5.7: Add `lontok.xyz` to the Railway service.
  - Runs on: dashboard.
  - Do: in the web service's Settings, under Networking, add the custom domain `lontok.xyz`, then `www.lontok.xyz`. If Railway asks for a port, use the one in the deploy log's `Uvicorn running on http://0.0.0.0:<port>` line. Copy the records Railway lists for each domain: a CNAME target and a TXT record named `_railway-verify`.
  - Why: Railway only serves a domain, and only issues its certificate, once the domain is on the service and DNS points at it.
  - Check: both domains appear on the service as waiting for DNS. Paste the records into this step's result line.
  - Undo: remove the two custom domains from the service.

- [ ] Step 5.8: Move the DNS records at Cloudflare.
  - Runs on: Cloudflare dashboard, for the `lontok.xyz` zone.
  - Do: write down the two current A records first. Add the `_railway-verify` TXT records from 5.7. Then replace the A record for `lontok.xyz` with a CNAME to Railway's target, and do the same for `www`. Leave Proxy status on DNS only (grey cloud), the way the A records are now.
  - Why: Cloudflare flattens a CNAME on the apex, so `lontok.xyz` can point at Railway's target. Staying DNS only lets Railway issue its own certificate and keeps Cloudflare out of the path, which matches today.
  - Check: `dig +short lontok.xyz` and `dig +short www.lontok.xyz` no longer print `20.112.93.148`. Within a few minutes, both domains show as verified on the Railway service with a certificate.
  - Undo: delete the CNAME and TXT records and restore the A records for `lontok.xyz` and `www` to `20.112.93.148`. The VM still has its Certbot certificate, so it serves HTTPS again as soon as DNS returns.

- [ ] Step 5.9: Check `lontok.xyz` on Railway.
  - Runs on: laptop.
  - Do:

    ```bash
    for host in lontok.xyz www.lontok.xyz; do
      curl -s -o /dev/null -w "$host %{http_code} %{remote_ip}\n" "https://$host/health"
    done
    for path in / /experience /projects /projects/career-platform /skills /education /contact; do
      curl -s -o /dev/null -w "$path %{http_code}\n" "https://lontok.xyz$path"
    done
    curl -s https://lontok.xyz/ | grep -o '<link rel="stylesheet" href="[^"]*"'
    curl -s https://lontok.xyz/ | grep -c "Greg Lontok"
    ```

  - Why: This confirms visitors now reach Railway, with a valid certificate and working links.
  - Check: every request returns `200`, and `remote_ip` isn't `20.112.93.148`. The stylesheet link starts with `https://lontok.xyz/static/`, and the name count is at least 1. Open the site in a browser once to see the styles load. If you used `curl` earlier and got old answers, your machine cached the old DNS for up to five minutes, so wait and rerun.
  - Undo: step 5.8's undo.

- [ ] Step 5.10: Record the results and update the docs.
  - Do: add a dated result line under each step, check off the boxes, and update the progress line at the top. If 5.5 needed the `.venv/bin/` fix, update `deploy/railway.md` to match.

## Not in this plan

- Shutting down the VM or deleting its SQLite file. The VM stays as the fallback until Greg retires it. Once DNS moves, Certbot's renewal on the VM will fail, since `lontok.xyz` no longer reaches it. The current certificate keeps working for a fallback until it expires.
- Removing `greglontok.com` and `www.greglontok.com` from the service. They serve this app after step 5.5 until someone removes them.
- Renaming the Railway project or service away from "rehearsal."
- Deleting the `lontok/career-platform-rehearsal` repo.
