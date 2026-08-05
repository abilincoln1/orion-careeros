# ORION Platform / CareerOS -- Architecture Overview

## Scope of this document
This describes the ORION Platform + CareerOS foundation as actually
built (Sprint 1, Sprint 1 Closure's platform restructure, and the
Career DNA Service -- see `docs/adr/0004-career-dna-domain-model.md`),
plus how the remaining approved high-level service architecture (Job
Intelligence, Recruiter Intelligence, Company Intelligence, Matching
Engine, Application Studio, Interview Studio, Communication Hub,
Analytics Engine, Learning Intelligence, Document Generation) will
attach to it in later, separately-authorised sprints. Career DNA is the
foundational data layer those later services will read from; no
business logic for the AI/matching/generation services themselves
exists yet.

**ORION is the platform. CareerOS is a product built on it.** This
distinction, introduced at Sprint 1 Closure by Chief Architect directive,
is why the repository is split into `/platform` and `/products/careeros`
rather than treating CareerOS's backend as the whole system. See
`docs/platform/PLATFORM_KERNEL.md` for the full capability list and
`docs/adr/0002-orion-platform-restructure.md` for why this split exists
and what alternatives were rejected.

## System shape

```
/platform/kernel/orion_kernel     -- ORION Platform Kernel (shared, product-agnostic)
  config.py       OrionBaseSettings: every product's Settings subclasses this
  logging.py      structured logging, identical across products
  security.py     password hashing + JWT primitives, parametrized by product settings
  database.py     async engine/session/get_db construction + shared readiness check
  middleware.py   RequestContextMiddleware (request id, timing, logging)
  health.py       build_health_router(): /health, /health/live, /health/ready

/products/careeros/backend/app    -- CareerOS product code
  core/           thin bindings of orion_kernel to CareerOS's own Settings/engine
  models/         SQLAlchemy ORM models -- the seed of the Career Knowledge Graph
  schemas/        Pydantic request/response contracts, separate from ORM models
  api/v1/         versioned HTTP surface (auth, health), each service its own router module
  main.py         wires config, logging, database, auth, health, and the API router together
```

CareerOS's `app/core/*` modules do not reimplement configuration,
logging, security, database wiring, or health endpoints -- they bind the
kernel's generic factories to CareerOS's own `Settings`, database engine,
and `get_db` dependency. A second ORION product would follow the same
five-file pattern against its own settings and models, without touching
CareerOS's code. This is enforced, not just documented: the kernel is
checked (via `scripts/metrics/collect_metrics.py`) to never import
product code.

Sprint 1's original models (`app/models` -- Sprint 1 defines only `User`)
remain the seed of the Career Knowledge Graph; later, authorised sprints
add Skill, Experience, Project, Technology, Employer, Recruiter, Company,
Application, Interview, LearningGoal, and CareerPolicy as first-class
related tables, never as documents.

## Data flow

```
Client (React/Vite, or curl/Postman)
    -> FastAPI (products/careeros/backend/app/main.py)
        -> RequestContextMiddleware (orion_kernel.middleware -- request id, timing, logging)
        -> CORS
        -> API router (/api/v1)
            -> /health, /health/live, /health/ready   (orion_kernel.health, bound to CareerOS's db/settings)
            -> /auth/register, /auth/login, /auth/refresh, /auth/me
        -> SQLAlchemy async session (app/core/database.py, built from orion_kernel.database factories)
            -> PostgreSQL (Docker service "db")
```

Alembic migrates the schema out-of-band (via a sync psycopg2 connection to
the same Postgres instance) before the app starts; see
`docker-compose.yml`'s backend command.

## How the Career Knowledge Graph will attach

Per the Engineering Constitution, CVs/cover letters/etc. are **generated
outputs**, never the source of truth. The `users` table is the anchor
node ("Candidate"). Subsequent, separately-authorised sprints add:

- Career DNA Service -> Skill, Experience, Project, Technology tables,
  each foreign-keyed to `users.id`.
- Job Intelligence Service -> a connector-per-source architecture (Indeed,
  Reed, NHS Jobs, etc.), each independently implementing fetch / validate /
  normalise / deduplicate / health-status, writing into a shared
  `job_postings` table so connector failures never cascade. Shared
  connector-framework infrastructure would live in
  `platform/shared_connectors` (currently reserved, not implemented).
- Recruiter Intelligence, Company Intelligence -> Recruiter and Company
  tables, related to job postings and to the user's interaction history.
- Matching Engine -> reads Candidate + Job + Company + Recruiter graph,
  applies configurable weights (see `config/config.example.yaml`), and
  writes explainable match records (score + reasoning per factor).
- Document Generation Service -> reads only from the knowledge graph to
  render CVs/cover letters/etc.; it has no independent data store. Shared
  rendering infrastructure would live in `platform/shared_services`
  (currently reserved, not implemented).

## Configuration philosophy

Platform-wide configuration (server, database, auth, CORS, logging)
lives in `OrionBaseSettings` (`platform/kernel/orion_kernel/config.py`);
every product subclasses it and overrides only its own defaults.
CareerOS's `Settings` (`products/careeros/backend/app/core/config.py`)
does exactly this. Domain configuration (salary bands, commute radius,
matching weights, company watchlists, learning priorities) is out of
scope for the current code but its intended shape is documented in
`config/config.example.yaml` so later sprints extend rather than invent
configuration conventions.

## Authentication framework

JWT-based (access token 30 min default, refresh token 7 days default, both
configurable), implemented once in `orion_kernel.security` and bound to
each product's own settings. Passwords hashed with bcrypt via `passlib`.
No automatic sending of emails/applications/messages exists anywhere in
the codebase -- consistent with the "Human Approval" principle, auth only
establishes identity, it never triggers outbound action. Authorization
(roles/permissions) is a documented but not-yet-implemented Platform
Kernel responsibility -- see `docs/platform/PLATFORM_KERNEL.md`.

## Observability

- Structured logs (JSON or plain-text, configurable) with request ID,
  path, method, status code, and duration on every request
  (`orion_kernel.logging` + `orion_kernel.middleware`).
- `/api/v1/health` -- static liveness info (service name/version/env).
- `/api/v1/health/live` -- liveness probe.
- `/api/v1/health/ready` -- readiness probe; returns 503 if the database is
  unreachable, suitable for Docker `HEALTHCHECK` / k8s readiness probes in
  future deployments.
- `scripts/metrics/collect_metrics.py` -- code-quality/engineering
  metrics snapshot (coverage, complexity, dependency counts, security
  findings, architecture compliance); see `docs/METRICS.md`. This is a
  development-time metrics framework, not a runtime monitoring system --
  runtime Monitoring remains a documented, not-yet-implemented Platform
  Kernel responsibility.

## Deployment topology

Three Docker Compose services: `db` (Postgres 16), `backend` (FastAPI,
built from a repo-root context so it can install the ORION Platform
Kernel alongside CareerOS, runs Alembic migrations on boot then
`uvicorn --reload`), `frontend` (Vite dev server). All three run on a
single Windows host with no cloud dependency, satisfying "Docker First."
See `docs/adr/0002-orion-platform-restructure.md` for why the backend
build context is the repository root rather than
`products/careeros/backend` alone.

## Explicitly out of scope

AI/LLM integration, job-source scraping/connectors, CV/document
generation, matching logic, recruiter/company intelligence, communication
channels (email/WhatsApp/Telegram), and analytics. These are the subject
of subsequent, separately authorised sprints -- see
`docs/SPRINT-2-IMPLEMENTATION-PLAN.md` for what Sprint 2 is expected to
contain once authorised (planning only; not authorised as of Sprint 1
Closure).
