#!/usr/bin/env bash
set -euo pipefail

echo "Waiting for database..."
# Only wait if telemetry enabled and DATABASE_URL set
if [ "${TELEMETRY:-off}" = "on" ] && [ -n "${DATABASE_URL:-}" ]; then
  python - <<'PY'
import os, sys, time
import sqlalchemy as sa
url = os.environ["DATABASE_URL"]
for i in range(60):
    try:
        sa.create_engine(url).connect().close()
        print("DB is up.")
        sys.exit(0)
    except Exception:
        time.sleep(1)
print("DB still not reachable after 60s", file=sys.stderr)
sys.exit(1)
PY

  echo "Running Alembic migrations..."
  # Use your actual Alembic ini path
  alembic -c app/db/migrations/alembic.ini upgrade head
else
  echo "Skipping DB wait & migrations (TELEMETRY off or DATABASE_URL not set)."
fi

# Start API
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
