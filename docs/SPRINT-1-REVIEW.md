# Sprint 1 Engineering Review -- CareerOS (Project ORION)

> **Historical record, left as originally written.** This review was
> written before the ORION Platform restructure (Sprint 1 Closure, see
> `docs/adr/0002-orion-platform-restructure.md`), so file paths below
> (e.g. `backend/`, `frontend/`) refer to the pre-restructure top-level
> layout. The current layout is `products/careeros/backend` and
> `products/careeros/frontend`. See `docs/SPRINT-1-ACCEPTANCE-REPORT.md`
> for the up-to-date, post-restructure record.

**Date:** 2026-08-03
**Sprint scope:** Production-quality engineering foundation only (per Master
Engineering Prompt v2.0). No AI, scraping, matching, or document-generation
logic included by design.

## What was delivered

- **Docker Compose stack** (`docker-compose.yml`): `db` (Postgres 16),
  `backend` (FastAPI, auto-runs Alembic migrations on boot), `frontend`
  (Vite dev server). Runs entirely locally, no cloud dependency.
- **FastAPI backend** (`backend/app`): versioned API (`/api/v1`), CORS,
  structured request logging with request IDs, global exception handlers
  returning a consistent `{"error": {...}}` shape.
- **PostgreSQL + Alembic**: async SQLAlchemy 2.0 engine for the app
  (asyncpg), separate sync engine for migrations (psycopg2), initial
  migration creating the `users` table.
- **Authentication framework**: register / login / refresh / me endpoints,
  bcrypt password hashing, JWT access (30 min default) + refresh (7 day
  default) tokens, all expiry/algorithm values configurable.
- **Configuration management**: `pydantic-settings`-based `Settings` class,
  all values overridable via environment variables / `.env`; a documented
  placeholder (`config/config.example.yaml`) for the domain configuration
  (salary bands, commute radius, matching weights, watchlists, learning
  priorities) that later sprints will wire up -- nothing hardcoded.
- **Logging**: structured JSON or plain-text logs (configurable), request
  ID + timing + status code attached to every request via middleware.
- **Health monitoring**: `/health`, `/health/live`, `/health/ready` (the
  last checks live DB connectivity and returns 503 if unreachable).
- **React + TypeScript + Vite frontend**: minimal shell that calls the
  health endpoint and renders backend status, proving the "frontend
  consumes backend APIs" principle end-to-end.
- **Tests**: 12 pytest tests (unit + API) covering config, health, and the
  full auth flow (register, duplicate rejection, login, wrong password,
  unauthenticated access, refresh), run against in-memory SQLite so no
  Docker/Postgres is required to validate the suite.
- **Documentation**: `README.md` (setup/run/test instructions),
  `docs/ARCHITECTURE.md` (system design and how future services attach),
  `docs/API.md` (endpoint reference), `docs/adr/0001-*.md` (stack decision
  record).

## Acceptance checklist (against Sprint 1 requirements)

| Requirement | Status | Notes |
|---|---|---|
| Docker Compose | Done | `db` + `backend` + `frontend` services defined |
| FastAPI | Done | Versioned API, OpenAPI docs at `/docs` |
| PostgreSQL | Done | Postgres 16 service; async app driver (asyncpg) |
| Alembic | Done | Sync migration driver (psycopg2), initial `users` migration |
| Authentication framework | Done | JWT access+refresh, bcrypt hashing, no auto-send of anything |
| Configuration management | Done | All platform config via env vars; domain config documented as placeholder |
| Logging | Done | Structured, JSON/plain-text, request ID + timing |
| Health monitoring | Done | Liveness + readiness (DB-aware) + summary endpoint |
| Project structure | Done | `/backend /frontend /docs /docker /config /scripts /prompts /tests /data` |
| Developer documentation | Done | README, architecture, API reference, ADR |
| Unit tests | Done | 12 tests, all passing (verified this session) |
| API tests | Done | Full auth + health flow exercised via httpx AsyncClient |
| Migration validation | Partial | Migration reviewed and applied against SQLite-equivalent schema creation in tests; **not yet run against a live Postgres instance** (no Docker daemon available in this build environment -- see Known Limitations) |
| Docker verification | Partial | Compose file and Dockerfiles authored and reviewed; **not yet executed end-to-end** (no Docker daemon available in this build environment) |
| ADR governance | Done | ADR 0001 documents the stack decision |
| No AI/scraping/matching/doc-gen | Confirmed | None present in the codebase |

## Verification actually performed this session

- Installed all backend dependencies and ran the full pytest suite:
  **12/12 passed** (2 real bugs found and fixed in the process -- see below).
- Compiled every backend Python file with `py_compile`: no syntax errors.
- Imported the app's config/database/models modules directly and confirmed
  the `users` table registers correctly on SQLAlchemy's metadata.
- Installed frontend dependencies, ran `tsc -b` (zero type errors), and ran
  a production `vite build` (succeeded, 31 modules transformed).

## Bugs found and fixed during verification

1. **UUID/dialect mismatch**: `User.id` uses `postgresql.UUID(as_uuid=True)`,
   which expects a Python `uuid.UUID` object; the `/auth/me` and
   `/auth/refresh` code paths were comparing it directly against the raw
   string `sub` claim from the JWT, which works on Postgres (implicit
   cast) but breaks under SQLite in tests. Fixed by explicitly parsing the
   claim to `uuid.UUID` before querying, with a 401 on malformed input.
2. **Readiness check bypassed dependency injection**: `check_database_connection()`
   reached for the module-level async engine directly instead of the
   request-scoped session, so it always tested the real configured
   database rather than whatever session the request was actually using.
   This meant it couldn't be tested without a live Postgres instance, and
   more importantly wasn't a faithful readiness check. Fixed by having
   `/health/ready` inject the DB session via `Depends(get_db)` and passing
   it into the check function.

Both fixes are already applied in the delivered code and covered by the
existing test suite.

## Known limitations

1. **Not run against live Docker/Postgres.** This build/verification
   environment has no Docker daemon, so `docker compose up --build` has
   not been executed end-to-end. The Compose file, Dockerfiles, and
   Alembic migration have been reviewed line-by-line and the equivalent
   schema/queries are proven against SQLite in the test suite, but you
   should run `docker compose up --build` on your Windows/Docker Desktop
   machine as the first acceptance step before relying on this further.
2. **Default `SECRET_KEY` is a placeholder.** `.env.example` ships an
   obviously-insecure default; it must be replaced (`openssl rand -hex 32`)
   before any use beyond local development.
3. **No role-based authorization yet.** The auth framework establishes
   identity (register/login/refresh/me) but has no roles/permissions --
   appropriate for a single-user Sprint 1, will need addressing before
   multi-user SaaS.
4. **No rate limiting or account lockout** on login/register endpoints.
   Acceptable for local single-user use; should be added before any
   externally-reachable deployment.
5. **`config/config.example.yaml` is documentation, not enforced
   configuration.** It shows the intended shape of domain configuration
   (salary bands, commute radius, matching weights, watchlists, learning
   priorities) for the Matching Engine and related services, but nothing
   in Sprint 1's code reads it yet -- correct for this sprint's scope, but
   flagging so it isn't mistaken for already being wired up.
6. **Frontend is a placeholder shell**, not a dashboard. It exists only to
   prove the API-first / frontend-consumes-backend contract, per Sprint 1
   scope.

## Recommendations for Sprint 2

1. Run `docker compose up --build` on the target Windows machine and
   confirm `alembic upgrade head` applies cleanly against real Postgres,
   then re-run the pytest suite pointed at that Postgres instance for
   full parity with the SQLite-based run already verified.
2. Rotate `SECRET_KEY` and commit a real `.env` (untracked) before any
   further work.
3. Begin the Career DNA Service: add Skill, Experience, Project, and
   Technology tables related to `users`, as the first real expansion of
   the Career Knowledge Graph -- this is the natural next ADR-worthy
   architectural step.
4. Decide (and record as an ADR) whether Job Intelligence connectors will
   be separate deployables or modules within the existing backend before
   writing the first connector, since that shapes the service boundary.
5. Add CI (even a minimal GitHub Actions workflow running `pytest` and
   `tsc -b`) now, while the surface area is still small, rather than
   retrofitting it later.

## Authorization requested

Sprint 1 is complete and verified per the checklist above. Requesting
authorization to proceed to Sprint 2 (Career DNA Service + Career
Knowledge Graph expansion), or direction to address any of the known
limitations first.
