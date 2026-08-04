#!/usr/bin/env bash
# Run the CareerOS backend test suite against a real PostgreSQL instance
# (Sprint 1 Postgres-parity gate; see docs/SPRINT-1-ACCEPTANCE-REPORT.md).
#
# Usage against Docker Compose's "db" service:
#   TEST_DATABASE_URL="postgresql+asyncpg://careeros:careeros@localhost:5432/careeros" \
#     ./scripts/run_tests_postgres.sh
#
# The target database is used as scratch space: tables are created and
# dropped by the test fixtures on every run. Do not point this at a
# database containing real data.
set -euo pipefail

if [ -z "${TEST_DATABASE_URL:-}" ]; then
  echo "TEST_DATABASE_URL is not set. Example:"
  echo '  export TEST_DATABASE_URL="postgresql+asyncpg://careeros:careeros@localhost:5432/careeros"'
  exit 1
fi

cd "$(dirname "$0")/.."
pip install -e platform/kernel --quiet
cd products/careeros/backend
pytest -v
