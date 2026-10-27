#!/bin/sh
set -e

# Run database migrations for managed databases (e.g. Postgres on RDS).
# For SQLite/dev the app also creates tables on startup, so failures here
# are non-fatal unless RUN_MIGRATIONS=1 is explicitly set.
if [ "${RUN_MIGRATIONS:-0}" = "1" ]; then
  echo "Running alembic migrations..."
  alembic upgrade head
fi

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
