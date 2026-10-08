# Railway deployment

The web service in the Railway project `career-platform-rehearsal` builds this
repo from `main` with Railpack and serves `lontok.xyz`. `railway.json` holds
its settings, so a change there ships with the next push. Settings in the
dashboard are overridden by it.

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
