# Tasks 4–7 controlled batch report

**Date:** 2026-09-17
**Worktree:** `/workspaces/career-platform/.worktrees/fastapi-resume-site`
**Branch:** `feat/fastapi-resume-site`
**Implementation commit:** `d4dc0c4 feat: complete resume site release readiness`

## Scope completed

This batch resolved the two Task 4 review findings, implemented the Task 5
acceptance/regression coverage, added the Task 6 deployment assets and runbook,
and documented and executed the Task 7 release verification sequence. Approved
specifications and implementation plans were not modified. No remote operation,
merge, or push was performed.

## Preflight and baseline

The supplied directory was confirmed to be a linked Git worktree on
`feat/fastapi-resume-site`; its Git directory differs from the shared Git common
directory and it is not a submodule.

Initial command:

```bash
uv run pytest -q
```

Baseline result: **26 passed, 1 failed**. The failing
`test_unknown_project_returns_not_found` made a request against the un-migrated
developer database. `ResumeService.get_project_by_slug` correctly converted its
SQLite `no such table: projects` `OperationalError` to an outage, so the route
returned 503 rather than the intended missing-project 404. This reproduced the
reported Task 4 test-isolation problem.

## TDD evidence

### Task 4 lazy database factory and route isolation

Before production changes, the following new/modified route tests were written:

- `test_page_dependency_uses_database_url_configured_before_app_creation`
- `test_unknown_project_returns_not_found(client)`
- fallback and generic-outage acceptance tests using a real isolated app fixture

Initial Task 5 test command:

```bash
uv run pytest tests/test_content_visibility.py tests/test_fallback.py -q
```

It failed as expected before the fixture existed: the new route tests had no
`client` fixture, and the lazy-factory regression test made a request to a
schema/seeded SQLite file configured immediately before `create_app()` but
received **503** from the previously import-captured default database.

After implementing the fixture and lazy factory wiring:

```bash
uv run pytest tests/test_pages.py tests/test_content_visibility.py tests/test_fallback.py -q
```

Result: **12 passed**.

### Task 6 deployment assets

The deployment asset and release-check tests were written before the deployment
files and README changes:

```bash
uv run pytest tests/test_deploy_assets.py -q
```

Initial result: **3 failed**. The Nginx/systemd files were absent and the README
did not contain the release checks. After implementation:

```bash
uv run pytest tests/test_deploy_assets.py -q
```

Result: **4 passed**.

The manual backup drill exposed an additional protection gap: SQLite's
`.backup` command produced a **0644** file despite the script's `umask`. A
behavioral regression test was added before the fix:

```bash
uv run pytest tests/test_deploy_assets.py::test_backup_creates_a_restricted_verified_database_copy -q
```

Initial result: failed with `420 == 384` (0644 instead of 0600). The minimal
fix explicitly applies `chmod 600` immediately after `.backup`; the same test
then passed.

## Task 4 review fixes

1. **Lazy database session factory:** `app/routers/pages.py` no longer imports
   or captures `SessionLocal`. `create_app()` reads `Settings` at factory time,
   builds an engine/session factory for that configured URL, and stores both on
   `app.state`. The route dependency resolves `request.app.state.session_factory`
   when a request is wired. This keeps router, application, and database
   responsibilities separated and introduces no import cycle. The regression
   test proves a database URL changed before `create_app()` supplies published
   content to `/projects`.
2. **Real missing-project database test:** `tests/conftest.py` creates an
   isolated file-backed SQLite database for every test, sets `DATABASE_URL`
   before creating the test application, creates the schema from metadata, and
   disposes the engine at teardown. The unknown-project test now uses that
   migrated database and exercises the actual public route/service missing-row
   behavior, producing 404 independently of `data/resume.db`.

The fixture supplies `app`, `client`, `session`, and `seeded_session`.
`seeded_session` uses the idempotent public seed data and no fixture accesses
the developer database.

## Task 5 coverage and documentation

- Added public HTML coverage that inserts an unpublished skill into the isolated
  real database and confirms it cannot render on `/skills`.
- Added a route-level 503 test through FastAPI's dependency override. It
  confirms the response contains the generic temporary-unavailability message
  and never includes a SQLite error detail.
- Added a homepage outage test using the real `ResumeService` fallback path. It
  confirms fallback profile content remains available while featured-project
  and detailed-resume navigation/content are absent.
- Preserved the existing service coverage for published filters, list ordering,
  project routing, fallback validity, and optional-content rendering.
- Added the requested README manual accessibility checklist: keyboard-only
  navigation, visible focus, readable mobile layout, one primary heading,
  descriptive links, and no empty optional labels.

## Task 6 deployment implementation

### Assets

- `deploy/nginx/career-platform.conf` redirects HTTP to HTTPS and proxies only
  to `http://127.0.0.1:8000`, with standard forwarded headers.
- `deploy/systemd/career-platform.service` runs as the dedicated
  `career-platform` non-root user, reads
  `/etc/career-platform/environment`, uses `/srv/career-platform` as its
  checkout working directory, binds Uvicorn only to `127.0.0.1:8000`, and uses
  restrictive `UMask=0077` plus basic service hardening.
- `deploy/scripts/backup-sqlite.sh` validates exactly two arguments, creates
  and restricts the backup directory, performs SQLite `.backup`, verifies
  `PRAGMA integrity_check`, forces resulting backup mode 0600, and prints its
  path.
- `deploy/scripts/restore-sqlite.sh` validates its arguments, rejects an
  existing target or SQLite sidecar, copies with mode 0600, verifies integrity,
  and removes the target on failure.
- `deploy/scripts/deploy.sh` requires `DATABASE_URL`, backs up before a
  dependency sync, migration, and seed operation, and fails fast at every
  step.

All deployment scripts were syntax-checked and committed executable:

```bash
bash -n deploy/scripts/backup-sqlite.sh \
  deploy/scripts/restore-sqlite.sh \
  deploy/scripts/deploy.sh
stat -c '%a %n' deploy/scripts/*.sh
```

Result: all syntax checks passed; each script is mode **755**.

### Documentation and protected storage

`deploy/README.md` provides an ordered beginner-oriented Azure VM guide:
creation of an Ubuntu VM; an NSG restricted to SSH/HTTP/HTTPS; dependency
installation; service user and protected persistent directories; clone and
environment setup; migration and seed; backup-before-deploy; systemd and Nginx
activation; standalone Certbot issuance; public and private health checks; and
a non-destructive restore drill. It explicitly instructs operators not to
expose port 8000.

The production `DATABASE_URL` is documented as
`sqlite:////var/lib/career-platform/resume.db`, outside the checkout. The
environment example clarifies that production configuration belongs only in
`/etc/career-platform/environment`. `.gitignore` now protects SQLite files and
their journal/WAL/SHM sidecars globally, and ignores local verification backup
directories.

## Backup/restore integrity evidence

The required migration and seed were executed, then a real application database
was backed up and restored. The task brief's `/tmp` paths were intentionally
replaced with the Git-ignored project-local
`data/backup-verification/` path because this execution environment prohibits
temporary-directory file operations.

```bash
uv run alembic upgrade head
uv run python -m app.seed
bash deploy/scripts/backup-sqlite.sh data/resume.db "$backup_dir"
bash deploy/scripts/restore-sqlite.sh "$backup_file" "$restore_target"
sqlite3 "$restore_target" "PRAGMA integrity_check;"
stat -c '%a %n' "$backup_file" "$restore_target"
```

Final result:

```text
ok
600 .../resume-20260917T215522Z-40626.db
600 .../restored-resume.db
Verification backup artifacts removed.
```

The initial verification artifacts were also removed. The ignored local
`data/resume.db` was retained rather than deleting a pre-existing developer
database.

## Task 7 release verification

README now records the exact required release checklist:

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

The sequence through the test command was executed:

```bash
uv sync --all-groups && mkdir -p data && uv run alembic upgrade head && \
uv run python -m app.seed && uv run ruff format --check . && \
uv run ruff check . && uv run pytest -q
```

Result: dependencies checked, migration/seed completed, format and lint passed,
and **35 passed** tests completed.

Uvicorn was then started on `127.0.0.1:8000` for a bounded smoke test. The
following responses were manually checked:

```text
200 /
200 /experience
200 /projects
200 /projects/career-platform
200 /skills
200 /education
200 /health
404 /projects/no-such-project
{"status":"ok"}
```

The server was stopped by its specific PID after the smoke test and a subsequent
connection check confirmed it was no longer serving.

## Final validation

Fresh pre-commit quality gate:

```bash
uv run ruff format --check . && uv run ruff check . && uv run pytest -q && \
git diff --check
```

Result:

```text
34 files already formatted
All checks passed!
35 passed, 2 warnings in 0.81s
```

The two warnings are existing FastAPI/Starlette TestClient deprecation warnings
from installed dependencies; no test failures, lint errors, formatting changes,
or diff whitespace errors occurred.

## Changed files

```text
.env.example
.gitignore
README.md
app/db/session.py
app/main.py
app/routers/pages.py
deploy/README.md
deploy/nginx/career-platform.conf
deploy/systemd/career-platform.service
deploy/scripts/backup-sqlite.sh
deploy/scripts/restore-sqlite.sh
deploy/scripts/deploy.sh
tests/conftest.py
tests/test_content_visibility.py
tests/test_deploy_assets.py
tests/test_fallback.py
tests/test_pages.py
```

## Self-review

- Confirmed the router has no import-time `SessionLocal` capture, database URL
  configuration is resolved by the factory, and the regression uses a real
  seeded SQLite file.
- Confirmed all public collection/detail behavior continues to use the existing
  published-only SQLAlchemy service queries; no broad exception handlers or
  raw visitor-derived SQL were added.
- Confirmed generic route failures do not expose the injected SQLite detail and
  homepage fallback continues to omit detailed content.
- Confirmed backup/restore scripts quote arguments, validate argument counts,
  reject destructive restore targets, validate integrity, and produce 0600
  database files. The shell syntax checks and behavioral backup test exercise
  these properties.
- Confirmed Nginx's only upstream is loopback, systemd's only Uvicorn host is
  loopback, production storage is outside the checkout, scripts are executable,
  and no certificate, secret, or database file was staged.
- Reviewed staged changes with `git diff --cached --check`; executable file
  modes were included in the commit.

## Remaining operator considerations

`your-domain.example`, `YOUR_DOMAIN`, `YOUR_EMAIL`, repository URL, Azure
administrator name, and Azure location are deliberate runbook placeholders and
must be replaced by the deployer. The required app runtime and all automated
checks are complete; no code concerns remain.

## Final review fixes — 2026-09-17

The final review findings were corrected in the same worktree and branch.
Approved specifications and plans were not changed; no push or merge was
performed.

### Azure clone ownership

The Azure runbook now creates `/srv` explicitly as `root:root` and creates the
empty `/srv/career-platform` destination as `career-platform:career-platform`
before executing the clone as the non-root service account:

```bash
sudo install -d -m 755 -o root -g root /srv
sudo install -d -m 750 -o career-platform -g career-platform /srv/career-platform
sudo -u career-platform git clone YOUR_REPOSITORY_URL /srv/career-platform
```

This keeps `/srv` root-owned while allowing `git clone` to use its already
owned, empty target directory.

### Stable seed identities and public-profile invariant

`profiles`, `skills`, `experiences`, `projects`, and `education` now have
nullable, unique `seed_key` values for seed-managed records. The seed payload
uses stable identifiers that are not derived from public display fields. Every
upsert now finds records by its key, so a changed profile email, experience
start date, skill name, project slug, or education display field updates the
existing record rather than creating a duplicate. Keys absent from a later seed
payload are reconciled by unpublishing only the corresponding seed-managed
row.

The migration backfills the original public seed rows, then creates a SQLite
partial unique index allowing only one `profiles.published = 1` row. The seed
also unpublishes any prior public profile before publishing its selected
profile, preserving the invariant for the full table rather than relying on
`ORDER BY ... LIMIT 1` selection.

Regression tests were first run before the implementation. The changed-email
and changed-start-date test failed because the former natural identities
created a second public profile and experience:

```text
Left contains one more item: ('alex.parker.updated@example.com', True)
```

After the key-based implementation, it asserts that both database tables and
the public `ResumeService` result contain exactly the current email and start
date. A second regression removes all seed-managed skills, experiences,
projects, and education between runs and proves the records no longer appear
in any published homepage collection. The model regression verifies that
inserting a second published profile raises the database `IntegrityError`.

The deployed local database was migrated and reseeded:

```bash
uv run alembic upgrade head
uv run python -m app.seed
uv run alembic current
```

Result: `20260917_02 (head)`. Direct SQLite verification after seeding reported
one published profile and the expected stable keys:

```text
published_profiles
------------------
                 1
profile:primary  alex.parker@example.com          1
experience:west-coast-commerce:analytics-engineering-intern  2026-06-01  1
project:career-platform        1
```

### Safe public project URLs

`app.core.urls.normalize_http_url` accepts only Pydantic-validated HTTP(S)
URLs and returns `None` for non-strings, `javascript:`, `data:`, relative, and
otherwise malformed values. Seed validation rejects invalid repository or live
demo URLs before a session is opened, preventing unsafe source content from
being written. Read-service queries sanitize stored project URLs as a defense
for pre-existing or externally ingested records. The project-detail Jinja
template applies the same validator immediately before generating each
external link, so a malformed object returned by an alternate service path
cannot render an unsafe `href`.

The seed regression parameterizes `javascript:alert(1)`,
`data:text/html,unsafe`, and `not a valid URL`, asserting the seed raises
before any project is inserted. The service regression verifies stored unsafe
schemes and malformed values are returned as `None` while
`https://demo.example.com` remains available. The route regression injects
unsafe values through the service boundary and proves the project-link list,
unsafe scheme, and malformed text are all absent from the HTML.

### Homepage impact summary

The homepage now renders an `Impact summary` section directly after the
profile introduction and immediately before the Experience section. It contains
only accomplishment metrics from the already published experience query; the
seeded evidence is **“6 hours saved per week”** for automated weekly KPI
reporting. The outer non-fallback guard keeps this detailed section absent
during database-outage fallback responses.

The homepage route regression verifies the heading order:

```text
profile headline < Impact summary < home-experience-heading
```

and asserts the metric is visible. A real database route regression adds an
unpublished accomplishment with `99% private impact` and confirms that private
metric cannot appear while the published seed metric does. The fallback route
test confirms `Impact summary` is absent.

### Backup/restore integrity and final verification

After migration and seeding, the production-shaped local database was backed
up and restored using the deployment scripts under a project-local transient
directory, avoiding prohibited system temporary directories. The restored copy
passed SQLite integrity verification and both artifacts had restrictive modes:

```text
ok
600 data/final-review-backup/resume-20260917T220546Z-47066.db
600 data/final-review-backup/restored-resume.db
```

The backup, restored database, and empty verification directory were removed
immediately after the check.

Final required quality gate:

```bash
uv run ruff format --check .
uv run ruff check .
uv run pytest -q
```

Result: **36 files already formatted**, **All checks passed**, and
**44 passed** in 1.05 seconds. The test command emitted only the two existing
FastAPI/Starlette TestClient dependency deprecation warnings.
