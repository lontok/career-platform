#!/usr/bin/env bash
set -euo pipefail

if [[ "$#" -ne 2 ]]; then
    echo "Usage: $0 <database-path> <backup-directory>" >&2
    exit 64
fi

if [[ -z "${DATABASE_URL:-}" ]]; then
    echo "DATABASE_URL must be set for migration and seeding." >&2
    exit 78
fi

script_directory="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
"$script_directory/backup-sqlite.sh" "$1" "$2"

uv sync --locked --no-dev
uv run alembic upgrade head
uv run python -m app.seed

echo "Deployment preparation complete. Restart the career-platform service."
