# ORION Platform

ORION is the reusable engineering platform. **CareerOS is a product built
on it** -- CareerOS is not itself the platform (see
`docs/ARCHITECTURE.md` and `docs/platform/PLATFORM_KERNEL.md`).

CareerOS is a Personal AI Career Operating System: a Career Intelligence
Platform that continuously understands a professional, analyses the
employment market, recommends the highest-value opportunities, prepares
evidence-based applications, and learns from outcomes. It is the first
product on the ORION Platform; the platform exists so that future
products don't reimplement authentication, configuration, logging, health
monitoring, and database wiring from scratch.

**Status:** Sprint 1 delivered CareerOS's engineering foundation. Sprint 1
Closure additionally established the ORION Platform architecture,
governance, risk/technical-debt registers, and a metrics framework, per
Chief Architect directive -- see `docs/SPRINT-1-ACCEPTANCE-REPORT.md`.
A subsequent "Docker Build Review & Sprint 2 Readiness" directive
verified repository independence from other projects on this machine
(e.g. NDIP), audited and hardened the Docker setup for multi-project use,
and added a one-command bootstrap script -- see
`docs/SPRINT-2-READINESS-REPORT.md`. The Career DNA Service (Person,
Employment/Role, Skill/Competency, Evidence -- 24 entities across 4
API routers) is implemented and under active engineering review; see
`docs/adr/0004-career-dna-domain-model.md` for the architecture and
`docs/Sprint1.6-Candidate-Acceptance-Review.md` for its current
acceptance status. AI/matching/document-generation logic (which
consumes Career DNA data, rather than being Career DNA itself) remains
deferred -- see `docs/ARCHITECTURE.md` for what's still out of scope
and why.

**This repository is one of several independent projects that may live on
the same machine** (e.g. alongside `NDIP` under `C:\Projects`). It does
not depend on, reference, or share configuration with any sibling
project -- see `docs/REPOSITORY_INDEPENDENCE_REPORT.md`.

## Project structure

```
/platform            ORION Platform Kernel (orion_kernel) + reserved shared-code locations
  /kernel               Implemented: config, logging, security, database, health, middleware
  /shared_services      Reserved, documented, not implemented
  /shared_libraries     Reserved, documented, not implemented
  /shared_connectors    Reserved, documented, not implemented
/products
  /careeros
    /backend            FastAPI application (consumes orion_kernel), Alembic migrations, pytest suite
    /frontend           React + TypeScript + Vite shell (consumes the backend API)
/governance           Engineering Constitution, architecture/process/quality standards
/docs                 Architecture, API reference, ADRs, reports, registers, metrics
/scripts              bootstrap.ps1 (one-command onboarding) + Unix dev-convenience scripts
/config               Non-secret domain configuration (example/future shape)
/prompts              Reserved for AI prompt templates (future sprints)
/tests                Reserved for cross-product/integration tests (future sprints)
/data                 Reserved for local data artifacts (future sprints, gitignored)
```

`/prompts`, `/tests`, and `/data` are intentionally empty placeholders
(each holds a `.gitkeep` so they survive version control) -- not dead
directories. An unused `/docker` directory left over from before
`docker-compose.yml` moved to the repo root (ADR 0002) was removed during
the Docker audit; see `docs/DOCKER_AUDIT_REPORT.md`.

## Prerequisites

- Docker Desktop (Windows), with Docker Compose v2
- (Optional, for running things outside Docker) Python 3.12+, Node 20+

## Quick start (Docker -- recommended)

**One command** (Windows PowerShell):

```powershell
.\scripts\bootstrap.ps1
```

This checks Docker Desktop/Compose/Git/Python, creates `.env` from
`.env.example` if missing, builds and starts the stack, runs migrations,
and polls the health endpoints until the backend actually responds. See
`docs/DEVELOPER_GUIDE.md` for details, troubleshooting, and what to do if
a port is already taken by another project on this machine.

Equivalent manual steps, if you'd rather not use the script:

```bash
cp .env.example .env
# Edit .env and set a real SECRET_KEY:
#   openssl rand -hex 32
docker compose up --build
```

This starts three services (container/network names all follow the
`orion-careeros-*` pattern so they don't collide with other projects on
this machine -- see `docs/adr/0003-docker-naming-and-multi-project-isolation.md`):

- `db` -- PostgreSQL 16, host port `5432` by default (override with
  `POSTGRES_PORT` in `.env`)
- `backend` -- FastAPI, host port `8000` by default (override with
  `BACKEND_PORT`; installs the ORION Platform Kernel, runs
  `alembic upgrade head` automatically, then starts; docs at
  `http://localhost:8000/docs`)
- `frontend` -- Vite dev server, host port `5173` by default (override
  with `FRONTEND_PORT`)

Verify the platform is healthy:

```bash
curl http://localhost:8000/api/v1/health
curl http://localhost:8000/api/v1/health/ready
```

**Docker verification status:** `docker compose up --build` has been run
end-to-end twice on the target Windows/Docker Desktop machine -- the
first run caught a real `CORS_ORIGINS` parsing bug (fixed, see TD-R06),
the second confirmed a clean startup with Docker's own `HEALTHCHECK`
passing (see TD-R07). The subsequent naming/port hardening in this
section has been validated as correct config and re-tested at the
application layer, but should be confirmed with one more live run --
see `docs/SPRINT-2-READINESS-REPORT.md`.

## Running the backend outside Docker (optional)

```bash
cd products/careeros/backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt   # installs orion-kernel from ../../../platform/kernel automatically
cp .env.example .env   # or set DATABASE_URL to a local Postgres instance
alembic upgrade head
uvicorn app.main:app --reload
```

## Running tests

```bash
./scripts/run_tests.sh              # in-memory SQLite, no Docker/Postgres required
./scripts/run_tests_postgres.sh      # against a real PostgreSQL instance (set TEST_DATABASE_URL first)
```

## Database migrations

Migrations are managed with Alembic (`products/careeros/backend/alembic/`).
To create a new migration after changing a model:

```bash
cd products/careeros/backend
alembic revision --autogenerate -m "describe the change"
alembic upgrade head
```

The initial migration (`0001_create_users_table`) creates the `users`
table -- the first node of the Career Knowledge Graph.

## Configuration

All platform configuration is via environment variables (see
`.env.example`, `platform/kernel/orion_kernel/config.py` for the shared
base, and `products/careeros/backend/app/core/config.py` for CareerOS's
overrides); nothing is hardcoded. Domain configuration (salary bands,
commute radius, matching weights, company watchlists, learning
priorities) is documented as a placeholder in `config/config.example.yaml`
for the sprints that implement those services.

## Governance

`/governance` holds the Engineering Constitution and the process/quality
standards every change is expected to follow: `ARCHITECTURE_PRINCIPLES.md`,
`ADR_INDEX.md`, `SPRINT_APPROVAL_PROCESS.md`,
`ARCHITECTURE_REVIEW_PROCESS.md`, `DEFINITION_OF_DONE.md`,
`QUALITY_GATES.md`, `CONTRIBUTION_STANDARDS.md`, `CODING_STANDARDS.md`,
`REPOSITORY_STANDARDS.md`.

## Documentation index

- `docs/ARCHITECTURE.md` -- system design, data flow, platform/product split
- `docs/DEVELOPER_GUIDE.md` -- day-to-day dev workflows, troubleshooting, port-collision handling
- `docs/platform/PLATFORM_KERNEL.md` -- Platform Kernel responsibilities (implemented vs. documented)
- `docs/API.md` -- CareerOS Sprint 1 API surface
- `docs/adr/` -- architecture decision records (see `governance/ADR_INDEX.md`)
- `docs/SPRINT-1-REVIEW.md` -- Sprint 1 engineering review
- `docs/SPRINT-1-ACCEPTANCE-REPORT.md` -- Sprint 1 Closure acceptance report (Postgres/Docker verification, governance, registers, metrics, repository review)
- `docs/REPOSITORY_INDEPENDENCE_REPORT.md` -- confirms no dependency on sibling projects (e.g. NDIP)
- `docs/DOCKER_AUDIT_REPORT.md` -- full Docker config audit (naming, ports, portability)
- `docs/SPRINT-2-READINESS-REPORT.md` -- readiness checklist ahead of Sprint 2 authorization
- `docs/SPRINT-2-IMPLEMENTATION-PLAN.md` -- Sprint 2 planning only (not authorised for implementation)
- `docs/TechnicalDebt.md`, `docs/RiskRegister.md`, `docs/METRICS.md` -- living registers
- `docs/CareerOS_Sprint1_Compliance_Report.docx` -- formal compliance report

## Status

Sprint 1 Closure complete. Docker Build Review & Sprint 2 Readiness work
complete, pending one live Docker re-verification and Chief Architect
authorization for Sprint 2. See `docs/SPRINT-2-READINESS-REPORT.md` for
the full checklist and outstanding items.
