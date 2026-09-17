# Career Platform

A database-driven personal resume website for analytics and technical roles.

## Run locally in Codespaces

```bash
uv sync --all-groups
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Visit `/health` to confirm the application is running.