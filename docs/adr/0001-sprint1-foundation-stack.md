# ADR 0001: Sprint 1 Foundation Technology Choices

## Status
Accepted

## Problem
Sprint 1 requires a production-quality engineering foundation (API framework,
persistence, migrations, auth, config, logging, health monitoring) that the
full CareerOS platform (Career Knowledge Graph, Matching Engine, Job
Intelligence connectors, etc.) will be built on top of in later sprints. The
stack must run entirely locally on Windows via Docker Compose with no cloud
dependency, and must not require architectural rework as domain services are
added.

## Options Considered
1. **FastAPI + SQLAlchemy 2.0 (async) + PostgreSQL + Alembic** (chosen)
2. Django + Django REST Framework + PostgreSQL
3. Node.js (NestJS) + TypeORM + PostgreSQL
4. Flask + SQLAlchemy + PostgreSQL

FastAPI was selected because: it is API-first by design (matches the "API
First" constitution principle, auto-generates OpenAPI docs at `/docs`); async
SQLAlchemy scales well to the I/O-bound workloads expected from job-source
connectors and AI calls in later sprints; Pydantic gives strong, explicit
schema validation which supports the "Explainability" and "Truth First"
principles (structured, typed data in and out); and the ecosystem
(Alembic, pytest, uvicorn) is mature and Docker-friendly.

Django was rejected as too opinionated/monolithic for a service-oriented
architecture (Career DNA, Job Intelligence, Matching Engine, etc. as
distinct services). NestJS was rejected only because the approved stack
specifies Python for the backend. Flask was rejected in favor of FastAPI's
native async support and OpenAPI generation.

## Decision
Adopt FastAPI + SQLAlchemy 2.0 (async, via asyncpg) + PostgreSQL 16 +
Alembic (sync, via psycopg2, for migrations only) as the backend foundation,
containerized with Docker Compose (`db`, `backend`, `frontend` services).
Authentication uses JWT (access + refresh) with `passlib[bcrypt]` for
password hashing, issued by an internal auth framework rather than a
third-party IdP, to keep Sprint 1 fully local/offline per the "Docker
First" principle. Multi-user SSO can be layered in later without breaking
the token contract.

## Consequences
- Alembic migrations run with a separate sync driver (psycopg2) from the
  app's async engine (asyncpg) against the same Postgres instance. This is
  a well-established SQLAlchemy pattern but means two connection strings
  must be kept in sync in configuration (`DATABASE_URL` / `DATABASE_URL_SYNC`).
- The `users` table is the first node of the future Career Knowledge Graph.
  Sprint 2+ services (Career DNA, Job Intelligence, etc.) must model new
  entities as first-class tables/relationships, not as JSON blobs, honoring
  the "model around structured knowledge, not documents" principle.
- JWT secret (`SECRET_KEY`) must be rotated to a strong random value before
  any non-local deployment; the default in `.env.example` is intentionally
  insecure and clearly marked as such.
- No frontend framework decision beyond "React + TypeScript + Vite" was
  needed since that was already specified in the approved stack.
