# FastAPI Resume Site Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a recruiter-focused, database-driven personal resume website using FastAPI, Jinja templates, plain CSS, and SQLite, with a profile fallback when the database is unavailable.

**Architecture:** The application is one server-rendered FastAPI modular monolith. Route handlers call focused read services, which query SQLite through SQLAlchemy and return only published data. The homepage switches to a validated, version-controlled fallback profile only for database failures; all detailed content is unavailable until the database recovers.

**Tech Stack:** Python 3.12+, uv, FastAPI, Uvicorn, Jinja2, SQLAlchemy 2.x, Alembic, SQLite, pytest, HTTPX/TestClient, plain CSS, Nginx, systemd, Azure VM.

**Spec:** `docs/superpowers/specs/2026-09-15-career-platform-resume-site.md`

## Global Constraints

- Develop and run the application locally in GitHub Codespaces before deploying to an Azure VM.
- Use `uv` for dependencies, virtual environments, and the lockfile.
- Use FastAPI with Jinja templates and plain CSS; do not introduce a JavaScript frontend framework.
- Use SQLite for the first release. Configure the database-file path through `DATABASE_URL`; keep the Azure VM database file outside the application directory.
- Only server-side application code accesses SQLite.
- Normal public pages render only database records where `published = true`.
- The fallback is a version-controlled, validated, public-only profile. Use it only for a homepage database error.
- During a database outage, do not show experience, projects, skills, or education from a fallback or stale source.
- Never commit secrets, tokens, private contact details, or database files.
- Use parameterized SQLAlchemy queries; never construct SQL from visitor input.
- Provide responsive, semantic, keyboard-navigable pages with descriptive links and adequate contrast.
- Configure Azure VM HTTPS with Nginx in front of Uvicorn, and run Uvicorn through systemd.
- Back up the SQLite database file to a protected location before every deployment or schema migration; document and locally test restoration.

---

## Planned File Structure

| Path | Responsibility |
| --- | --- |
| `pyproject.toml` / `uv.lock` | Reproducible Python project and dependencies |
| `app/main.py` | FastAPI factory, static files, templates, routers, and error handlers |
| `app/core/config.py` | Environment-based settings, including `DATABASE_URL` |
| `app/db/base.py` / `app/db/session.py` | SQLAlchemy metadata, engine, and request-safe session factory |
| `app/models/*.py` | Database tables and relationships |
| `app/schemas/content.py` | Typed display models and fallback-profile validation |
| `app/services/resume.py` | Published-content read queries and homepage fallback policy |
| `app/routers/pages.py` | Public route handlers and route-parameter validation |
| `app/templates/*.html` | Shared layout and page templates |
| `app/static/styles.css` | Responsive site styling |
| `app/seed.py` / `app/fallback_profile.json` | Repeatable demo content and fallback snapshot |
| `alembic/` / `alembic.ini` | Schema migration configuration and revisions |
| `tests/` | Unit, service, and route-level regression tests |
| `.env.example` / `.gitignore` | Safe local configuration and ignored local state |
| `README.md` | Codespaces setup, content updates, local backup/restore, and Azure VM deployment |
| `deploy/` | Nginx, systemd, backup, restore, and deployment scripts/configuration |

### Task 1: Bootstrap the FastAPI Project

**Files:**
- Create: `pyproject.toml`, `.python-version`, `.gitignore`, `.env.example`
- Create: `app/__init__.py`, `app/main.py`, `app/core/__init__.py`, `app/core/config.py`
- Create: `app/templates/base.html`, `app/templates/not_found.html`, `app/static/styles.css`
- Create: `tests/__init__.py`, `tests/test_health.py`
- Modify: `README.md`

**Interfaces:**
- Produces `create_app() -> FastAPI` in `app.main`.
- Produces `Settings.database_url: str` in `app.core.config`.
- Later tasks register routers and database lifecycle behavior through `create_app`.

**Done looks like:** `uv run uvicorn app.main:app --reload` starts in Codespaces, `/health` returns JSON `{"status": "ok"}`, and the application can serve a template and static CSS file.

**How to check it:** Run `uv run pytest tests/test_health.py -q`, then run `uv run uvicorn app.main:app --host 0.0.0.0 --port 8000` and visit `/health` plus `/static/styles.css`.

- [ ] **Step 1: Initialize the uv project and add runtime/test dependencies**

```bash
uv init --python 3.12
uv add fastapi "uvicorn[standard]" jinja2 sqlalchemy alembic pydantic-settings
uv add --dev pytest httpx ruff
uv lock
```

- [ ] **Step 2: Write the failing health-route test**

```python
# tests/test_health.py
from fastapi.testclient import TestClient

from app.main import create_app


def test_health_returns_ok() -> None:
    response = TestClient(create_app()).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 3: Run the test to verify it fails**

Run: `uv run pytest tests/test_health.py -q`  
Expected: FAIL because `app.main` and `create_app` do not exist.

- [ ] **Step 4: Implement settings and the minimal application factory**

```python
# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./data/resume.db"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
```

```python
# app/main.py
from fastapi import FastAPI
from fastapi.responses import JSONResponse


def create_app() -> FastAPI:
    app = FastAPI()

    @app.get("/health")
    def health() -> JSONResponse:
        return JSONResponse({"status": "ok"})

    return app


app = create_app()
```

- [ ] **Step 5: Add the template/static configuration and safe local defaults**

Create the Jinja environment and mount `/static`; add a semantic `base.html` with a skip link, primary navigation placeholder, and `{% block content %}`. Add `not_found.html` extending the base layout. Add `.env.example` with `DATABASE_URL=sqlite:///./data/resume.db`, ignore `.env`, `.venv/`, `data/*.db`, `*.sqlite3`, and Python caches. Document the Codespaces startup command in `README.md`.

- [ ] **Step 6: Run formatting, linting, and the task test**

Run: `uv run ruff format . && uv run ruff check . && uv run pytest tests/test_health.py -q`  
Expected: formatting and linting succeed; the health test passes.

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml uv.lock .python-version .gitignore .env.example app tests README.md
git commit -m "feat: bootstrap FastAPI resume application"
```

### Task 2: Define and Migrate the SQLite Resume Data Model

**Files:**
- Create: `app/db/__init__.py`, `app/db/base.py`, `app/db/session.py`
- Create: `app/models/__init__.py`, `app/models/profile.py`, `app/models/experience.py`, `app/models/project.py`, `app/models/skill.py`, `app/models/education.py`
- Create: `alembic.ini`, `alembic/env.py`, `alembic/script.py.mako`, `alembic/versions/20260915_01_create_resume_tables.py`
- Create: `tests/test_models.py`
- Modify: `app/main.py`, `README.md`

**Interfaces:**
- Produces `Base` metadata and `SessionLocal` from `app.db`.
- Produces SQLAlchemy models `Profile`, `Experience`, `ExperienceAccomplishment`, `Project`, `Skill`, and `Education`.
- Produces association tables `experience_skills` and `project_skills`.
- Later tasks use model fields and relationships exactly as defined here.

**Done looks like:** A fresh SQLite file can receive an Alembic migration that creates all content tables and foreign-key relationships. A model test can create a project and associate it with a skill.

**How to check it:** Set `DATABASE_URL=sqlite:///./data/test.db`, run `uv run alembic upgrade head`, inspect with `sqlite3 data/test.db ".tables"`, then run `uv run pytest tests/test_models.py -q`.

- [ ] **Step 1: Write failing model and relationship tests**

```python
# tests/test_models.py
from app.models.project import Project
from app.models.skill import Skill


def test_project_can_have_skills() -> None:
    project = Project(
        slug="revenue-dashboard",
        title="Revenue Dashboard",
        summary="Dashboard for weekly sales decisions.",
        problem="Sales reporting was delayed.",
        contribution="Built the reporting model.",
        methods="SQL and Python",
        published=True,
    )
    skill = Skill(name="SQL", category="analytics", published=True)

    project.skills.append(skill)

    assert project.skills == [skill]
```

- [ ] **Step 2: Run the model test to verify it fails**

Run: `uv run pytest tests/test_models.py -q`  
Expected: FAIL because the models are not defined.

- [ ] **Step 3: Implement focused SQLAlchemy models**

Use SQLAlchemy 2.x typed mappings. Include these required fields:

```python
# app/models/project.py (field contract)
slug: Mapped[str]  # unique, indexed, URL-safe value
title: Mapped[str]
summary: Mapped[str]
problem: Mapped[str]
contribution: Mapped[str]
methods: Mapped[str]
outcome: Mapped[str | None]
repository_url: Mapped[str | None]
live_demo_url: Mapped[str | None]
published: Mapped[bool]
featured: Mapped[bool]
display_order: Mapped[int]
```

Define all remaining spec fields on their matching models. `ExperienceAccomplishment` references `experiences.id` with `ondelete="CASCADE"`. Association tables enforce unique pairs with a composite primary key. Set SQLite `PRAGMA foreign_keys=ON` for every connection.

- [ ] **Step 4: Configure Alembic and create the initial migration**

Set `target_metadata` to `Base.metadata`, read `DATABASE_URL` from settings, and generate a revision named `create_resume_tables`. The migration must create every model and association table, indexes for project slug and published/listing queries, and required foreign keys.

```bash
uv run alembic revision --rev-id 20260915_01 --autogenerate -m "create resume tables"
uv run alembic upgrade head
```

- [ ] **Step 5: Run migration and model checks**

Run: `rm -f data/test.db && DATABASE_URL=sqlite:///./data/test.db uv run alembic upgrade head && uv run pytest tests/test_models.py -q`  
Expected: migration completes and model test passes.

- [ ] **Step 6: Document schema initialization**

Add exact commands to create `data/`, run migrations, and explain that the SQLite file must not be committed.

- [ ] **Step 7: Commit**

```bash
git add app/db app/models alembic alembic.ini tests/test_models.py app/main.py README.md
git commit -m "feat: add SQLite resume data model"
```

### Task 3: Seed Content, Validate the Fallback, and Implement Published Reads

**Files:**
- Create: `app/schemas/__init__.py`, `app/schemas/content.py`, `app/services/__init__.py`, `app/services/resume.py`
- Create: `app/seed.py`, `app/fallback_profile.json`
- Create: `tests/test_resume_service.py`, `tests/test_seed.py`
- Modify: `README.md`

**Interfaces:**
- Produces `PublicProfile`, `HomepageContent`, and `FallbackProfile` Pydantic models.
- Produces `ResumeService.get_homepage() -> HomepageContent`.
- Produces `ResumeService.get_project_by_slug(slug: str) -> Project | None`.
- Raises `DatabaseUnavailableError` only when the service cannot query SQLite.
- `get_homepage()` returns fallback-only content for a database failure; it does not use fallback for successful empty queries.

**Done looks like:** The seed command creates representative published records for every content type. Service methods return only published data, order experience correctly, reject unpublished project slugs, and return the validated fallback profile only after a simulated database failure.

**How to check it:** Run `uv run alembic upgrade head && uv run python -m app.seed`, then `uv run pytest tests/test_seed.py tests/test_resume_service.py -q`.

- [ ] **Step 1: Write failing service tests**

```python
# tests/test_resume_service.py
def test_homepage_uses_fallback_only_when_database_fails(monkeypatch) -> None:
    service = ResumeService(session_factory=raising_session_factory)

    homepage = service.get_homepage()

    assert homepage.is_fallback is True
    assert homepage.profile.headline
    assert homepage.experiences == []
    assert homepage.projects == []
    assert homepage.skills == []
    assert homepage.education == []


def test_unpublished_project_is_not_returned(session) -> None:
    session.add(Project(slug="private-work", title="Private", summary="x",
                        problem="x", contribution="x", methods="x",
                        published=False))
    session.commit()

    assert ResumeService(lambda: session).get_project_by_slug("private-work") is None
```

- [ ] **Step 2: Run the service tests to verify they fail**

Run: `uv run pytest tests/test_resume_service.py tests/test_seed.py -q`  
Expected: FAIL because the service, schemas, seed module, and fallback do not exist.

- [ ] **Step 3: Define validation models and the fallback snapshot**

Create a strict `FallbackProfile` Pydantic model with required `full_name`, `headline`, `summary`, `location`, `target_roles`, and at least one public contact link. Reject unknown fields and malformed `http`/`https` URLs. Store only deliberately public example values in `app/fallback_profile.json`; no secrets or private data.

- [ ] **Step 4: Implement seed validation and idempotent demo seeding**

`python -m app.seed` must validate the fallback file before writing. It must insert or update one published profile, at least one published experience, one experience accomplishment, one published featured project, one published skill, and one published education record. It must reject duplicate project slugs and invalid references before committing.

- [ ] **Step 5: Implement the read service**

Use `select()` statements with bound parameters. Filter all public collection and detail queries by `published.is_(True)`. Sort current experience first and then by most recent start date; sort projects and skills by `display_order`. Catch only SQLAlchemy `OperationalError` and `SQLAlchemyError` around database access, log with `logger.exception`, and raise `DatabaseUnavailableError`. Load the fallback JSON only in `get_homepage()` after this error.

- [ ] **Step 6: Run the seed and service tests**

Run: `uv run alembic upgrade head && uv run python -m app.seed && uv run pytest tests/test_seed.py tests/test_resume_service.py -q`  
Expected: seed data is created; all tests pass.

- [ ] **Step 7: Document safe content updates**

Document the sequence: backup database, edit/update seed data, run migration if needed, run seed, and confirm public routes. State that ordinary resume updates must not require template edits.

- [ ] **Step 8: Commit**

```bash
git add app/schemas app/services app/seed.py app/fallback_profile.json tests README.md
git commit -m "feat: add published resume content service"
```

### Task 4: Build Public Routes, Outage Handling, and Semantic Templates

**Files:**
- Create: `app/routers/__init__.py`, `app/routers/pages.py`
- Create: `app/templates/home.html`, `app/templates/experience.html`, `app/templates/projects.html`, `app/templates/project_detail.html`, `app/templates/skills.html`, `app/templates/education.html`, `app/templates/error.html`
- Modify: `app/main.py`, `app/templates/base.html`, `app/static/styles.css`
- Create: `tests/test_pages.py`

**Interfaces:**
- Consumes `ResumeService` and `DatabaseUnavailableError`.
- Produces public handlers for `/`, `/experience`, `/projects`, `/projects/{slug}`, `/skills`, and `/education`.
- Uses `project_detail.html` only with a published project returned by `get_project_by_slug`.

**Done looks like:** All specified public URLs render semantic HTML from database-backed service data. Invalid or unpublished project slugs render a 404 page. A homepage database failure renders the fallback profile and outage message; a database failure on every other page renders a generic 503 error without details.

**How to check it:** Run `uv run pytest tests/test_pages.py -q`; manually inspect every route after seeding and use browser keyboard navigation through the main navigation.

- [ ] **Step 1: Write failing route tests**

```python
# tests/test_pages.py
def test_homepage_renders_fallback_for_database_failure(app_client, monkeypatch) -> None:
    monkeypatch.setattr("app.routers.pages.ResumeService.get_homepage",
                        lambda _: fallback_homepage_content())

    response = app_client.get("/")

    assert response.status_code == 200
    assert "temporarily unavailable" in response.text
    assert "Experience" not in response.text


def test_unknown_project_returns_not_found(app_client) -> None:
    response = app_client.get("/projects/no-such-project")

    assert response.status_code == 404
    assert "Page not found" in response.text
```

- [ ] **Step 2: Run the route tests to verify they fail**

Run: `uv run pytest tests/test_pages.py -q`  
Expected: FAIL because public routers and templates do not exist.

- [ ] **Step 3: Implement dependency wiring and handlers**

Add a service dependency that constructs `ResumeService(SessionLocal)`. Register the page router in `create_app`. Map `DatabaseUnavailableError` from `/` to the fallback homepage response. For all other public routes, map it to `error.html` with HTTP 503 and a generic “Please try again later” message. Map a missing project to `not_found.html` with HTTP 404.

- [ ] **Step 4: Implement templates and accessibility requirements**

Use a shared base template with one `<h1>` per page, a visible focus style, semantic `<header>`, `<nav>`, `<main>`, and `<footer>`, and a skip link to main content. Render external links with `target="_blank"` and `rel="noopener noreferrer"`. Omit optional fields and their labels together. In `home.html`, render no detailed-content sections when `is_fallback` is true.

- [ ] **Step 5: Add responsive plain CSS**

Use mobile-first CSS, a constrained readable content width, flexible card grids, visible keyboard focus, and a contrast-safe neutral palette. Include no external stylesheets or JavaScript dependencies.

- [ ] **Step 6: Run route tests, linting, and a local smoke test**

Run: `uv run ruff format . && uv run ruff check . && uv run pytest tests/test_pages.py -q && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000`  
Expected: automated checks pass; the seeded homepage and all navigation links load in a browser.

- [ ] **Step 7: Commit**

```bash
git add app/routers app/templates app/static app/main.py tests/test_pages.py
git commit -m "feat: render public resume pages"
```

### Task 5: Add End-to-End Content, Fallback, and Security Regression Coverage

**Files:**
- Create: `tests/conftest.py`, `tests/test_content_visibility.py`, `tests/test_fallback.py`
- Modify: `tests/test_pages.py`, `README.md`

**Interfaces:**
- Consumes the application factory, migration-created SQLite test database, seed module, routes, and `ResumeService`.
- Produces a stable test fixture that creates a disposable SQLite database per test session.

**Done looks like:** The test suite verifies all acceptance criteria that can be automated: published-only visibility, ordering, project routing, valid fallback behavior, omission of detailed fallback content, generic errors, and no broken optional links.

**How to check it:** Run `uv run pytest -q` and `uv run ruff format --check . && uv run ruff check .`; both commands exit successfully.

- [ ] **Step 1: Write the failing acceptance tests**

```python
# tests/test_content_visibility.py
def test_unpublished_records_never_render_in_public_html(client, seeded_session) -> None:
    seeded_session.add(Skill(name="Secret Skill", category="analytics", published=False))
    seeded_session.commit()

    response = client.get("/skills")

    assert response.status_code == 200
    assert "Secret Skill" not in response.text


# tests/test_fallback.py
def test_database_failure_on_projects_is_generic_503(client, monkeypatch) -> None:
    monkeypatch.setattr("app.routers.pages.get_resume_service", unavailable_service)

    response = client.get("/projects")

    assert response.status_code == 503
    assert "temporarily unavailable" in response.text
    assert "sqlite" not in response.text.lower()
```

- [ ] **Step 2: Run these tests to verify they fail**

Run: `uv run pytest tests/test_content_visibility.py tests/test_fallback.py -q`  
Expected: FAIL until fixtures and the full error/visibility behavior are in place.

- [ ] **Step 3: Implement reusable isolated SQLite fixtures**

Create `tests/conftest.py` that sets `DATABASE_URL` to a per-test temporary SQLite path before importing the application, enables SQLite foreign keys, creates schema through Alembic or metadata, seeds explicit test records, and supplies `client`, `session`, and `seeded_session` fixtures. The fixture must never use the developer's `data/resume.db`.

- [ ] **Step 4: Close test-discovered gaps without broad exception handling**

Make the smallest changes necessary for all tests. Preserve the policy: service code catches only SQLAlchemy database exceptions, logs them, and routes distinguish fallback homepage behavior from generic 503 behavior.

- [ ] **Step 5: Run the complete quality gate**

Run: `uv run ruff format --check . && uv run ruff check . && uv run pytest -q`  
Expected: all checks pass.

- [ ] **Step 6: Add a manual accessibility smoke-check list to the README**

Document these manual checks: keyboard-only navigation, visible focus, readable mobile layout, one main heading per page, descriptive link text, and no empty optional labels.

- [ ] **Step 7: Commit**

```bash
git add tests README.md app
git commit -m "test: cover public resume behavior"
```

### Task 6: Document and Automate Codespaces-to-Azure-VM Deployment

**Files:**
- Create: `deploy/nginx/career-platform.conf`, `deploy/systemd/career-platform.service`
- Create: `deploy/scripts/backup-sqlite.sh`, `deploy/scripts/restore-sqlite.sh`, `deploy/scripts/deploy.sh`
- Create: `deploy/README.md`
- Modify: `README.md`, `.env.example`, `.gitignore`
- Create: `tests/test_deploy_assets.py`

**Interfaces:**
- Consumes `DATABASE_URL` with a path outside the app checkout, such as `sqlite:////var/lib/career-platform/resume.db`.
- Produces an executable backup script accepting source database path and backup directory.
- Produces a restore script accepting a backup file and target database path.
- Produces Nginx and systemd configurations for a Uvicorn application bound only to `127.0.0.1:8000`.

**Done looks like:** A beginner can run the site in Codespaces, create and restore a local SQLite backup, and follow an exact Azure VM guide to deploy FastAPI behind Nginx with systemd. The documented production database path is persistent, protected, and outside the git checkout.

**How to check it:** Run `bash deploy/scripts/backup-sqlite.sh data/resume.db /tmp/resume-backups`, set `BACKUP_FILE` to the created `.db` file, then run `bash deploy/scripts/restore-sqlite.sh "$BACKUP_FILE" /tmp/restored.db` and compare `sqlite3` integrity checks. Run `uv run pytest tests/test_deploy_assets.py -q`.

- [ ] **Step 1: Write failing deployment-asset tests**

```python
# tests/test_deploy_assets.py
from pathlib import Path


def test_systemd_binds_uvicorn_to_loopback_only() -> None:
    service = Path("deploy/systemd/career-platform.service").read_text()

    assert "--host 127.0.0.1" in service
    assert "--port 8000" in service


def test_nginx_proxies_to_loopback() -> None:
    config = Path("deploy/nginx/career-platform.conf").read_text()

    assert "proxy_pass http://127.0.0.1:8000;" in config
```

- [ ] **Step 2: Run deployment-asset tests to verify they fail**

Run: `uv run pytest tests/test_deploy_assets.py -q`  
Expected: FAIL because deployment assets do not exist.

- [ ] **Step 3: Implement safe SQLite backup and restore scripts**

`backup-sqlite.sh` must exit on errors, validate exactly two arguments, create the backup directory if needed, run `sqlite3 "$SOURCE_DB" ".backup '$BACKUP_FILE'"`, run `PRAGMA integrity_check`, and print the created file path. `restore-sqlite.sh` must validate arguments, refuse to overwrite an existing target, copy the selected backup with restrictive permissions, and run `PRAGMA integrity_check`.

- [ ] **Step 4: Implement Azure VM service topology**

Create a systemd unit running `uv run uvicorn app.main:app --host 127.0.0.1 --port 8000` as a dedicated non-root `career-platform` user with `WorkingDirectory` set to the application checkout and `EnvironmentFile=/etc/career-platform/environment`. Create Nginx configuration that redirects port 80 to HTTPS and proxies HTTPS requests to `127.0.0.1:8000`; set standard forwarded headers. Keep certificate issuance as a documented Certbot command, never a committed certificate.

- [ ] **Step 5: Write the Codespaces and Azure VM runbook**

In `deploy/README.md`, provide ordered commands for: creating an Ubuntu Azure VM; allowing only SSH/HTTP/HTTPS in the network security group; installing Python, uv, Nginx, SQLite, and Certbot; creating `/var/lib/career-platform` owned by the service user; cloning the repository; setting `/etc/career-platform/environment` with the production `DATABASE_URL`; migration; seed; backup before deployment; systemd enable/restart; Nginx enable/reload; HTTPS certificate; health check; backup restore drill. Explain that port 8000 must not be exposed publicly.

- [ ] **Step 6: Execute local backup/restore and automated checks**

Run:

```bash
uv run alembic upgrade head
uv run python -m app.seed
bash deploy/scripts/backup-sqlite.sh data/resume.db /tmp/career-platform-backups
BACKUP_FILE="$(find /tmp/career-platform-backups -type f -name '*.db' -print -quit)"
bash deploy/scripts/restore-sqlite.sh "$BACKUP_FILE" /tmp/career-platform-restore.db
sqlite3 /tmp/career-platform-restore.db "PRAGMA integrity_check;"
uv run pytest tests/test_deploy_assets.py -q
```

Expected: backup and restore succeed, integrity check prints `ok`, and deployment-asset tests pass.

- [ ] **Step 7: Commit**

```bash
git add deploy README.md .env.example .gitignore tests/test_deploy_assets.py
git commit -m "docs: add Azure VM deployment runbook"
```

### Task 7: Run the Release Verification Checklist

**Files:**
- Modify: `README.md`

**Interfaces:**
- Consumes the complete seeded application, test suite, backup scripts, and deployment documentation.
- Produces a documented repeatable release-verification command sequence.

**Done looks like:** The repository has a clean, repeatable path from a new Codespaces checkout to a seeded local application, complete automated checks, and a verified backup/restore operation. The README records the exact release checks.

**How to check it:** In a fresh database path, complete the documented setup commands and run the release command sequence successfully.

- [ ] **Step 1: Add a failing release-check documentation assertion**

```python
def test_readme_lists_release_quality_commands() -> None:
    readme = Path("README.md").read_text()

    assert "uv run ruff check ." in readme
    assert "uv run pytest -q" in readme
    assert "backup-sqlite.sh" in readme
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_deploy_assets.py::test_readme_lists_release_quality_commands -q`  
Expected: FAIL until the release checklist is documented.

- [ ] **Step 3: Document and execute the release verification sequence**

Add this exact checklist to the README:

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

Then run the commands through `uv run pytest -q`; manually inspect `/`, `/experience`, `/projects`, one project URL, `/skills`, `/education`, `/health`, and an invalid project URL.

- [ ] **Step 4: Run the final automated quality gate**

Run: `uv run ruff format --check . && uv run ruff check . && uv run pytest -q`  
Expected: all commands pass.

- [ ] **Step 5: Commit**

```bash
git add README.md tests/test_deploy_assets.py
git commit -m "docs: add release verification checklist"
```

## Spec Coverage Review

| Spec area | Plan coverage |
| --- | --- |
| Recruiter-focused routes and content | Tasks 3 and 4 |
| SQLite tables, relationships, migrations, and seeds | Tasks 2 and 3 |
| Published-only public content | Tasks 3 and 5 |
| Homepage profile fallback and 503 behavior | Tasks 3, 4, and 5 |
| Validation, safe errors, privacy, and parameterized access | Tasks 2 through 5 |
| Semantic, responsive, accessible plain-CSS pages | Task 4 and Task 5 manual checks |
| Codespaces workflow, Azure VM, Nginx, systemd, SQLite persistence | Task 6 |
| Backup and restore | Task 6 and Task 7 |

## Plan Self-Review

- **Spec coverage:** Every acceptance criterion and global requirement maps to one or more tasks in the coverage table.
- **No placeholders:** The plan names concrete files, interfaces, commands, test assertions, deployment paths, and the explicit Alembic revision identifier `20260915_01`.
- **Type consistency:** `ResumeService`, `DatabaseUnavailableError`, `FallbackProfile`, `HomepageContent`, and `create_app` are defined before they are consumed by later tasks.
