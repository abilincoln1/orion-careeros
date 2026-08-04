#!/usr/bin/env bash
# Bring up the full local stack (Postgres + backend + frontend).
set -e
if [ ! -f .env ]; then
  echo "No .env found -- copying .env.example. Edit SECRET_KEY before real use."
  cp .env.example .env
fi
docker compose up --build
