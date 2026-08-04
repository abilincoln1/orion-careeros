#!/usr/bin/env bash
# Run Alembic migrations inside the running backend container.
set -e
docker compose exec backend alembic upgrade head
