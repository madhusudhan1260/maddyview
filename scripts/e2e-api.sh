#!/bin/sh
# Starts an isolated API for end-to-end tests on a throwaway database (never your real one).
set -e
cd "$(dirname "$0")/../backend"
DB=finpilot_e2e
URL="postgresql+psycopg://localhost:5432/$DB"
dropdb --if-exists "$DB"
createdb "$DB"
.venv/bin/alembic -x db_url="$URL" upgrade head >/dev/null
export FINPILOT_DATABASE_URL="$URL"
export FINPILOT_CORS_ORIGINS="http://localhost:5191,http://127.0.0.1:5191"
export FINPILOT_AUTH_RATE_LIMIT_PER_MINUTE=200
exec .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8041
