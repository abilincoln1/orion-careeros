# Baseline Engineering Report

**To:** Product Owner / Solution Architect / Chief Technical Architect
**From:** Claude Cowork, acting as Lead Engineer / DevOps Engineer, Project ORION
**Date:** 2026-08-05
**Re:** ORION Project Baseline — repository audit, Git baseline, documentation
structure, ADR folder, and Docker readiness verification, per the Claude
Cowork Engineering Constitution.

**Scope:** Verification and hygiene only. No application code was written
or modified. No architecture was changed. Where a gap was found, it was
either fixed directly (if safe and reversible — config/hygiene only) or
documented for explicit sign-off, per the constitution's "no hidden
assumptions" and "explain architectural decisions" principles.

**Current commit:** `8c59101` on `main`, 1 commit ahead of `origin/main`
(not pushed — pushing was not requested). Working tree clean.

---

## 1. Repository audit

The repository is more mature than a bare "baseline" — Sprint 1 and Sprint
1 Closure are already complete, committed, and documented. This audit
confirmed the actual file tree matches what the existing documentation
(`docs/ARCHITECTURE.md`, `governance/ADR_INDEX.md`) claims, with no drift.

| Area | Result |
|---|---|
| Platform/product split (`/platform`, `/products/careeros`) | Present and matches ADR 0002 |
| Backend (FastAPI/SQLAlchemy/Alembic) | Present; `app/api`, `core`, `models`, `schemas`, `repositories`, `services`, `tests`, 2 Alembic migrations |
| Frontend (React/TS/Vite) | Present; minimal shell, no substantial UI yet — consistent with docs |
| Governance (`/governance`) | 10 process documents present (constitution, standards, ADR index, quality gates, DoD, sprint approval) |
| Stray artefacts | One empty untracked directory `New folder` at repo root, and one empty untracked `docs/operations/`. Both are empty (git does not track empty directories, so they have no effect on the repository) and could not be removed in this session due to a filesystem permission restriction on the mounted path. Flagged for manual deletion. |
| Fabrication check | No employment history, qualifications, or achievements exist anywhere in this codebase yet (Career Knowledge Base models are schema-only, no seeded/fabricated data) — consistent with "CareerOS must never fabricate" |

Full structural breakdown is in `docs/PROJECT_BASELINE.md` §3 (written in
the prior baseline pass, still accurate — re-verified this session).

## 2. Git baseline

| Check | Result |
|---|---|
| Repository initialised | Yes |
| Branch | `main`, tracking `origin/main` |
| Commit history | `fc38096` (Sprint 1 baseline, 131 files) → `8c59101` (hygiene: `.gitignore` fix, tracked governing prompt, added `PROJECT_BASELINE.md` + `docs/sprints/`) |
| Working tree | Clean, no untracked or modified files |
| Secrets check | `.env` (real secrets file) is present on disk but correctly untracked and git-ignored; only `.env.example` (placeholder values, `SECRET_KEY` explicitly marked `CHANGE_ME`) is tracked |

No new commit was required this pass — the baseline was already
established in the prior session and re-verified clean here.

## 3. Documentation structure

| Path | Status |
|---|---|
| `/docs` | Present — architecture, API, developer guide, specs, risk register, technical debt register, metrics, sprint reports |
| `/docs/adr` | Present — ADR folder (see §4) |
| `/docs/sprints` | Present — created in the prior baseline pass as the canonical home for sprint docs from Sprint 2 onward (with `README.md` explaining why Sprint 1's docs remain at `docs/` root: ~32 existing cross-references) |
| `/docs/platform` | Present — Platform Kernel capability documentation |
| `/docs/diagrams` | Present — architecture diagram (Mermaid) |
| `/governance` | Present — constitution, coding standards, contribution standards, architecture principles, review process, quality gates, definition of done, sprint approval process |
| `docs/PROJECT_BASELINE.md` | Present — the baseline checkpoint document itself |

## 4. ADR folder

`docs/adr/` exists with three accepted ADRs, indexed in
`governance/ADR_INDEX.md`:

| ID | Title | Status |
|---|---|---|
| 0001 | Sprint 1 Foundation Technology Choices | Accepted |
| 0002 | Introduce the ORION Platform Architecture (Kernel + Products) | Accepted |
| 0003 | Docker Naming, Multi-Project Isolation, and Platform Kernel Distribution | Accepted (naming) / Deferred (kernel distribution) |

Directory is lowercase (`docs/adr/`, not `docs/ADR/`). This is a known,
documented deviation from the constitution's literal template — see
`docs/PROJECT_BASELINE.md` Finding 1 — kept as-is to avoid disrupting an
already-established, cross-referenced convention.

## 5. Docker readiness verification

No Docker daemon is available in this session's sandbox, so a live
`docker compose up --build` could not be re-run here. Two levels of
verification were performed instead:

**A. Static verification (performed this session):**

| Check | Result |
|---|---|
| `docker-compose.yml` YAML syntax | Valid (parsed successfully) |
| Services defined | `db` (postgres:16-alpine), `backend`, `frontend` |
| Referenced Dockerfiles exist | `products/careeros/backend/Dockerfile`, `products/careeros/frontend/Dockerfile` — both present |
| Referenced scripts/files exist | `scripts/init_db.sh`, `requirements.txt`, `package.json` — all present |
| Env vars referenced in Compose | `POSTGRES_USER/PASSWORD/DB`, `POSTGRES_PORT`, `BACKEND_PORT`, `FRONTEND_PORT`, `VITE_API_BASE_URL` — all defined or defaulted in `.env.example` (port overrides are intentionally commented out with in-file defaults) |
| Health checks | `db`: `pg_isready`; `backend` Dockerfile: `HEALTHCHECK` against `/api/v1/health`; `frontend`: none (documented as intentional — Vite dev server has no meaningful readiness signal and nothing depends on it) |
| Naming convention | `orion-careeros-*` for containers/image/network/volume, consistent with ADR 0003 |
| Restart policy | `unless-stopped` on all three services |
| No Windows-specific paths | Confirmed — no backslashes or drive letters in any Dockerfile or Compose file |
| Kernel install path | `-e ../../../platform/kernel` in `requirements.txt` resolves correctly given the Dockerfile's `COPY platform/kernel` + working-directory layout |

No discrepancies found. Configuration is unchanged since the prior
session's audit (`docs/DOCKER_AUDIT_REPORT.md`, 2026-08-04).

**B. Live verification (prior session, still valid):** `docs/TechnicalDebt.md`
(TD-R06, TD-R07) and `docs/RiskRegister.md` (RT-01, status **Closed**)
record that the user ran `docker compose up --build` twice on their
actual Windows/Docker Desktop machine — the second run, after a
`CORS_ORIGINS` parsing fix, started all three containers cleanly with no
crash loop, applied migrations, served the frontend, and the backend's
Docker `HEALTHCHECK` fired successfully against `/api/v1/health`. No
Compose or Dockerfile changes have been made since that run, so this
verification remains valid.

**Conclusion: Docker stack is ready.** Static config is correct and
consistent; live end-to-end startup was already confirmed by the user and
nothing has changed since.

## 6. Sign-off checklist

- [x] Repository audited — no drift between docs and actual tree, two
      harmless empty stray directories flagged for manual cleanup.
- [x] Git baseline confirmed — clean tree, linear history, secrets
      correctly excluded.
- [x] Documentation structure confirmed complete (`docs/`, `docs/adr/`,
      `docs/sprints/`, `governance/`).
- [x] ADR folder confirmed present and indexed (3 accepted ADRs).
- [x] Docker readiness verified — statically clean this session, live
      end-to-end success already on record and unchanged since.
- [x] No application code written or modified.
- [ ] **Pending Chief Technical Architect approval to proceed to Sprint 2**
      (per constitution: "Do not start the next sprint without approval").

## Open items carried forward (not blocking, not new)

These are pre-existing, already tracked, and unchanged by this report —
listed here only so this report is a complete, standalone snapshot:

- TD-006 / RT-03: no CI pipeline yet (recommended first Sprint 2
  prerequisite).
- TD-011 / RS-05: `python-jose` and transitive dependencies have known
  CVEs; migration to `PyJWT` evaluated but not yet done (correctly scoped
  as a dedicated task, not a baseline change).
- TD-012: `orion_kernel` cross-repository distribution not yet solved
  (zero urgency — only one product exists today).
- Two empty stray directories (`New folder`, `docs/operations/`) need
  manual deletion from outside this session.

Full detail on all of the above: `docs/TechnicalDebt.md`,
`docs/RiskRegister.md`.
