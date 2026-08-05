# Quality Gates

Concrete, checkable gates a change must pass. Where a gate cannot be
checked in the current environment (e.g. no Docker daemon available),
that must be stated explicitly rather than silently skipped.

| Gate | Check | Current baseline (Sprint 1 Closure) |
|---|---|---|
| Backend compiles | `python3 -m py_compile` on all `.py` files | Passing |
| Frontend type-checks | `npx tsc -b` | Passing, 0 errors |
| Frontend builds | `npx vite build` | Passing |
| Unit + API tests (SQLite) | `pytest -v` | 12/12 passing |
| Unit + API tests (Postgres) | `TEST_DATABASE_URL=... pytest -v` | 12/12 passing (verified via embedded PostgreSQL; see `docs/SPRINT-1-ACCEPTANCE-REPORT.md`) |
| Migration round-trip | `alembic upgrade head` -> `downgrade base` -> `upgrade head` against real Postgres | Verified |
| Live HTTP smoke test | real `uvicorn` process against real Postgres, hit over HTTP (not ASGI test transport) | Verified: root, health, health/live, health/ready, register, login, me all 200/201 |
| Docker Compose end-to-end | `docker compose up --build`, verify backend/frontend/db/networking | **Not yet run** -- no Docker daemon in the build/verification environment. Must be run by the user on the target Windows/Docker Desktop machine. Tracked in `docs/RiskRegister.md`. |
| Code coverage | `pytest --cov` | See `docs/METRICS.md` for current baseline |
| Cyclomatic complexity | `radon cc` | See `docs/METRICS.md` |
| Dependency count | manual count of `requirements.txt` / `package.json` | See `docs/METRICS.md` |
| Docker image size | `docker image ls` after build | **Not measured** -- requires Docker; see `docs/METRICS.md` |
| Security findings | dependency/CVE scan | **Not yet run** -- see `docs/TechnicalDebt.md` and `docs/RiskRegister.md` |
| Architecture compliance | manual review against `governance/ARCHITECTURE_PRINCIPLES.md` | See `docs/SPRINT-1-ACCEPTANCE-REPORT.md` Task 8 repository review |

A sprint cannot be marked closed while a gate shows "Not yet run" without
an explicit, named reason and a remediation owner (see
`docs/RiskRegister.md`).
