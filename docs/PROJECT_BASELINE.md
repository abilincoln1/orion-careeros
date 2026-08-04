# Project Baseline

**Purpose:** This document is the formal Project Baseline checkpoint
required by the Claude Cowork Engineering Constitution ("Current
Objective," pre-Sprint 2). It records the state of the repository as
verified on 2026-08-05, the actions taken to satisfy the baseline tasks,
and the findings from the repository audit. It supersedes nothing —
`docs/ARCHITECTURE.md` remains the authoritative architecture reference;
this document is the checkpoint record that confirms that reference is
accurate and that the repository is in a clean, governed state.

**Status:** Sprint 1 and Sprint 1 Closure are complete and committed.
Sprint 2 remains **not authorised** — see `docs/SPRINT-2-IMPLEMENTATION-PLAN.md`
(planning only). This baseline pass performed hygiene and documentation
tasks only; no application functionality was modified.

## 1. Git repository verification

| Check | Result |
|---|---|
| Repository initialised | Yes — `.git` present |
| Current branch | `main`, up to date with `origin/main` |
| Prior commits | 1 — `fc38096` "ORION CareerOS Sprint 1 baseline" (131 tracked files) |
| Working tree before this pass | Clean except one untracked file (`prompts/Claude Cowork Engineering Constitution.docx`) |
| Uncommitted work left behind | None — this pass commits everything it touched |

The repository already had a real initial commit from Sprint 1 baseline
work; this pass did not need to create one from scratch. It reviewed the
existing state, fixed hygiene gaps, and added the documents the
constitution requires before Sprint 2.

## 2. `.gitignore` review

The existing `.gitignore` was functional (Python, Node, `.env`, `.DS_Store`)
but had two gaps, both fixed in this pass:

- `products/careeros/backend/.coverage` (a generated pytest-cov data file)
  was tracked in the Sprint 1 commit. It has been removed from git
  tracking (`git rm --cached`) and `.coverage` / `.coverage.*` / `htmlcov/`
  / `*.cover` added to `.gitignore` so it can't recur.
- Added `.env.local`, `Thumbs.db`, `.idea/`, `.vscode/`, `*.swp` as
  standard hardening for a Windows/local-dev-first project, per the
  constitution's "no cloud dependency, primary environment Windows"
  requirement.

No other build artefacts, caches, or `node_modules` were found tracked —
the rest of the existing `.gitignore` was already effective.

## 3. Repository structure audit

```
/                        Repo root — governance and cross-cutting config
  .gitignore, .gitattributes, .dockerignore, .env.example, docker-compose.yml
  README.md               Entry point; project status and structure map

/governance               Binding process documents (constitution, standards,
                           ADR index, quality gates, definition of done,
                           sprint approval process) — the internal equivalent
                           of this Cowork constitution, already established
                           at Sprint 1 Closure.

/docs                      Architecture, API, developer guide, specs, reports.
  /adr                       Architecture Decision Records (lowercase path —
                              see Finding 1 below).
  /platform                  Platform Kernel capability documentation.
  /diagrams                  Mermaid architecture diagrams.
  /sprints                   NEW — canonical home for sprint docs from Sprint 2
                              onward (see Finding 2 below).

/platform                  ORION Platform Kernel — shared, product-agnostic code.
  /kernel/orion_kernel        config, logging, security, database, health,
                               middleware. Installed by CareerOS as an editable
                               local dependency (see ADR 0002, TD-012).
  /shared_connectors,
  /shared_libraries,
  /shared_services            Reserved for future products; documented, empty.

/products/careeros         The CareerOS product — the only product on ORION today.
  /backend                    FastAPI app: api/v1 (auth, health), core (thin
                               kernel bindings), models (SQLAlchemy — User is
                               the only table so far), schemas, repositories,
                               services, Alembic migrations, pytest suite
                               (test_auth, test_config, test_health).
  /frontend                   React + TypeScript + Vite shell (App.tsx,
                               main.tsx, api/client.ts); no substantial UI yet.

/config                    config.example.yaml — documents the shape of future
                           domain configuration (salary bands, matching
                           weights, etc.); not yet read by any code (TD-010).

/scripts                   bootstrap.ps1, dev_up.sh, init_db.sh, run_tests.sh,
                           run_tests_postgres.sh, run_migrations.sh,
                           metrics/collect_metrics.py.

/prompts                   Governing prompts, including this constitution.

/data, /tests              Reserved, currently just .gitkeep placeholders.
```

**Technology stack confirmed against actual dependency files:**

- Backend: Python, FastAPI 0.115.6, SQLAlchemy 2.0.36 (async, asyncpg),
  Alembic 1.14.0 (sync, psycopg2), Pydantic 2.10.4, python-jose (JWT),
  passlib/bcrypt, pytest 8.3.4.
- Frontend: React 18.3.1, TypeScript 5.6.3, Vite 5.4.11.
- Infra: Docker Compose — three services (`db` = Postgres 16, `backend`,
  `frontend`), `orion-careeros-*` naming per ADR 0003.
- Two Alembic migrations exist: `create_users_table`,
  `create_career_dna_schema`.

This matches what `docs/ARCHITECTURE.md`, `governance/ENGINEERING_CONSTITUTION.md`,
and the ADR set already describe — no drift found between documentation
and the actual tree.

## 4. Architecture documentation

`docs/ARCHITECTURE.md` (written at Sprint 1 Closure) was reviewed against
the current file tree and is accurate: the platform/product split, the
kernel's five bound modules, the data flow, and the "explicitly out of
scope" list all match what exists on disk. No update to that document was
needed as part of this baseline pass. It remains the primary architecture
reference; see also `docs/platform/PLATFORM_KERNEL.md` and
`governance/ADR_INDEX.md` for the three accepted ADRs.

## 5. Findings and deviations from a literal reading of the constitution

Documented explicitly, per "no hidden assumptions":

1. **ADR directory casing.** The constitution's template specifies
   `docs/ADR/`; the repository already uses `docs/adr/` (lowercase),
   established at Sprint 1 Closure and referenced by
   `governance/ADR_INDEX.md` and three existing ADRs. Renaming risks
   case-sensitivity issues on the Windows/cross-filesystem setup this
   project runs on (see `docs/REPOSITORY_INDEPENDENCE_REPORT.md`) for no
   real benefit. Kept as `docs/adr/`; flagged here rather than silently
   diverging.
2. **Sprint docs not moved into `docs/sprints/`.** The new `docs/sprints/`
   directory was created (with a `README.md` explaining the convention),
   but the existing Sprint 1 / Sprint 1 Closure documents were left in
   place at `docs/` root rather than moved, because at least 32
   cross-references to their current paths exist elsewhere in the repo.
   Moving them was judged out of scope for a hygiene/baseline pass — it
   would be a documentation-restructuring change, not a baseline
   verification. `docs/sprints/` is the convention for Sprint 2 onward.
3. **Stray empty directory.** An empty, untracked `New folder` exists at
   the repository root (likely left over from local file exploration on
   Windows). It contains nothing and git ignores empty directories, so it
   has no effect on the repository, but it could not be deleted from this
   session due to a filesystem permission restriction on the mounted
   path. Recommend deleting it manually from Windows Explorer.
4. **Constitution file now tracked.** `prompts/Claude Cowork Engineering
   Constitution.docx` was untracked (present on disk, not in git). Per
   the constitution's own Source of Truth priority ("Approved prompts"
   ranks above "Conversation history"), it has been added and committed
   so the governing prompt is part of the permanent project record.

## 6. Acceptance checklist

- [x] Git repository verified (exists, correct branch, clean history).
- [x] `.gitignore` reviewed, hardened, and a tracked generated-artifact
      (`.coverage`) removed from tracking.
- [x] Initial commit already existed from Sprint 1; this pass's changes
      are committed as a separate, clearly-labelled baseline commit (see
      commit log after this pass).
- [x] Repository structure audited (Section 3).
- [x] `docs/ADR/` requirement satisfied by pre-existing `docs/adr/`
      (Finding 1).
- [x] `docs/sprints/` created (Finding 2).
- [x] Current architecture documented — confirmed `docs/ARCHITECTURE.md`
      is accurate; no changes needed.
- [x] No application functionality modified.

## Known limitations of this pass

- No tests were executed (this was a documentation/hygiene baseline
  pass, not a verification sprint; the existing test suite and its last
  results are described in `docs/SPRINT-1-ACCEPTANCE-REPORT.md` and
  `docs/RiskRegister.md`).
- The stray `New folder` directory (Finding 3) needs manual deletion
  outside this session.
- Existing open risks and technical debt (`docs/RiskRegister.md`,
  `docs/TechnicalDebt.md`) are unchanged by this pass and remain the
  Lead Engineer / Security Engineer's responsibility to schedule.
