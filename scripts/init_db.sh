#!/usr/bin/env bash
# Runs once when the Postgres container's data volume is first created.
# Ensures required extensions are available before migrations run.
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-SQL
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
SQL
