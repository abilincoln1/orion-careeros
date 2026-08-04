# Docker Audit Report

**To:** Chief Architect
**From:** Claude, Chief Software Engineer, Project ORION
**Date:** 2026-08-04
**Re:** Task 2 of the "Docker Build Review & Sprint 2 Readiness" directive

Full review of `docker-compose.yml`, both Dockerfiles, build contexts,
bind mounts, health checks, restart policies, networks, volumes, and
environment variables. Findings are grouped by whether they required a
fix (applied directly, all safe/reversible) or are documented only.

## Findings fixed this session

| # | Area | Finding | Fix |
|---|---|---|---|
| 1 | Naming | Container/image/volume names used a bare `careeros_*` pattern with no platform prefix, and no explicit network name existed. Risk of collision with another project's generically-named containers. | Renamed to `orion-careeros-db` / `orion-careeros-backend` / `orion-careeros-frontend`, explicit `orion-careeros-network`, volume `orion-careeros-db-data`. Compose project name changed from `orion-platform` to `orion-careeros` (this file defines a product's stack, not the platform itself). See ADR 0003. |
| 2 | Ports | Host ports were hardcoded (`5432`, `8000`, `5173`). If another project on the same machine (e.g. NDIP) also wants these defaults, one of the two stacks fails to start. | Host-side ports are now `${POSTGRES_PORT:-5432}`, `${BACKEND_PORT:-8000}`, `${FRONTEND_PORT:-5173}` -- overridable via `.env`, defaults unchanged. Container-internal ports untouched. |
| 3 | Repository hygiene | An empty, unused `/docker` directory existed at the repo root -- a leftover from before `docker-compose.yml` moved to the root as part of ADR 0002. Not referenced anywhere; not part of the documented project structure in the README. | Removed. |
| 4 | Portability (line endings) | No `.gitattributes` existed. Shell scripts and Dockerfiles are currently LF (fine), but nothing enforces that if edited later on Windows -- CRLF line endings silently break `sh -c "..."` / shebang execution inside Linux containers. | Added `.gitattributes` forcing LF for `.sh`, `.py`, `Dockerfile`, `.yml`/`.yaml`, and CRLF for `.ps1` (the new bootstrap script, which must run natively on Windows). |

## Findings documented, not changed (with rationale)

| # | Area | Finding | Why not changed now |
|---|---|---|---|
| 5 | Build context | Backend build context is the repository root (not `products/careeros/backend`), so the Dockerfile can `COPY platform/kernel`. This is intentional (ADR 0002) and already reviewed there. `.dockerignore` at the root correctly scopes what's sent to the Docker daemon. | Correct as-is; re-confirmed the root-context `.dockerignore` excludes `.git`, `node_modules`, `__pycache__`, `.venv`, `outputs`, `.env`, etc. |
| 6 | Bind mounts | Backend mounts `./products/careeros/backend` and `./platform` into the container for live-reload; frontend mounts `./products/careeros/frontend` plus an anonymous `/app/node_modules` volume (correctly prevents the host's `node_modules` -- if present at all -- from shadowing the container's). All mount sources are relative paths. | Confirmed portable by the Task 4 relocation test; no host-absolute paths anywhere. |
| 7 | Health checks | `db` has a `pg_isready` healthcheck; `backend`'s `Dockerfile` has a `HEALTHCHECK` hitting `/api/v1/health` (confirmed firing successfully in the user's real `docker compose up --build` run -- TD-R07). `frontend` has no healthcheck. | Vite's dev server has no meaningful "ready" signal beyond the TCP port opening, and the frontend isn't a dependency of anything else in this stack (`backend` doesn't wait on it). Adding one would be cosmetic. Not implemented; noted here so it isn't mistaken for an oversight. |
| 8 | Restart policy | All three services use `restart: unless-stopped`, consistent. | Correct for local development; no change needed. |
| 9 | Volumes | Postgres data uses a named volume (not a host bind mount) -- correct, avoids any host-path dependency for persisted data. | No change needed. |
| 10 | Environment variables | `backend` uses both `env_file: .env` and an explicit `environment:` block that re-derives `DATABASE_URL`/`DATABASE_URL_SYNC` from the individual `POSTGRES_*` vars. This is intentional: it keeps the DB host (`db`, the Compose service name) authoritative even if a stale full URL is sitting in `.env`. | No change needed; documented here since it could look like duplication at a glance. |
| 11 | Windows path issues | Checked every script and Dockerfile for backslashes, drive letters, or `C:\`-style paths. None found -- Compose and Docker itself only ever see POSIX-style relative paths, translated by Docker Desktop's own Windows/WSL2 integration. | No change needed. |
| 12 | Platform Kernel install path | `requirements.txt`'s `-e ../../../platform/kernel` is relative and portable *within this repository*, confirmed by the Task 4 relocation test. It is **not** portable *across* repositories (a separate NDIP-style repo can't reach it). | This is an architecture question, not a Docker config bug -- covered in depth in `docs/adr/0003-docker-naming-and-multi-project-isolation.md` Decision 2 and TD-012, not duplicated here. |

## Verification performed
- `docker-compose.yml` re-validated as syntactically correct YAML (parsed
  with a YAML parser; structure inspected) after every naming/port
  change.
- Full backend test suite re-run after all changes: **12/12 passing**.
- Architecture compliance re-checked (0 kernel-imports-product-code
  violations).
- **Not independently re-verified with a live `docker compose up --build`
  in this session** (no Docker daemon in this environment, same
  limitation as prior sessions). The naming/port changes are config-only
  and don't touch application code, but per this project's Test First
  principle, they should still be confirmed with one more real run before
  being considered fully closed. **Action requested:** run
  `docker compose up --build` (or `.\scripts\bootstrap.ps1`) once more and
  confirm the three containers now come up as `orion-careeros-db`,
  `orion-careeros-backend`, `orion-careeros-frontend` on a network named
  `orion-careeros-network`.

## Conclusion
Four real portability/collision risks found and fixed directly (naming,
ports, dead directory, line-ending enforcement). One architectural gap
(cross-repository kernel distribution) found, correctly scoped as
"document, don't implement yet" per the directive, and tracked as TD-012
/ ADR 0003. Everything else audited was already correct and is recorded
here so the audit's completeness is visible, not just its findings.
