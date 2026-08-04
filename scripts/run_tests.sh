#!/usr/bin/env bash
# Run the CareerOS backend test suite (in-memory SQLite by default, no
# Docker/Postgres required). For a Postgres-parity run, set
# TEST_DATABASE_URL and see run_tests_postgres.sh.
set -e
cd "$(dirname "$0")/.."
pip install -e platform/kernel --quiet
cd products/careeros/backend
pytest -v
