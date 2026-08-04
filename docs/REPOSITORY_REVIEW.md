# Repository Review -- Sprint 1 Closure (Task 8)

A full read-through of `platform/kernel/orion_kernel` and
`products/careeros/backend/app` looking for duplicate code, weak naming,
future bottlenecks, layer violations, and unnecessary complexity, per the
Chief Architect directive. Findings are split into what was fixed
directly (safe, low-risk) and what is only documented (needs a dedicated
task, per `governance/ARCHITECTURE_REVIEW_PROCESS.md`).

## Fixed directly (safe improvements)

| Finding | Where | Fix |
|---|---|---|
| Duplicate logic: parsing a JWT `sub` claim into a `uuid.UUID`, tolerating malformed input, was implemented twice with slightly different code in `get_current_user` and `/auth/refresh`. | `app/api/deps.py`, `app/api/v1/auth.py` | Extracted a single `parse_user_id()` helper in `deps.py`; both call sites now use it. Re-ran the full test suite after the change (12/12 still passing). |
| Unused import: `oauth2_scheme` imported into `auth.py` but never referenced there (it's used by `deps.py`, which already imports it directly). | `app/api/v1/auth.py` | Removed the unused import. |
| Dead code: `app/schemas/health.py` defined `HealthStatus`/`ReadinessStatus`, which became redundant duplicates once those schemas moved into `orion_kernel.health` during the platform restructure. | `app/schemas/health.py` | Confirmed zero references (grepped the whole backend), then deleted. |
| Dead directory: `app/utils/` existed empty since initial scaffolding, never populated. | `app/utils/` | Deleted (empty dir, no risk). |
| Stale config: `products/careeros/backend/.dockerignore` stopped having any effect once the backend's Docker build context moved to the repository root (ADR 0002) -- Docker only reads `.dockerignore` from the build context root. | `products/careeros/backend/.dockerignore` | Removed; replaced by a root-level `.dockerignore` that actually applies. |

## Documented only (not safe to fix incidentally)

| Finding | Where | Why not fixed now | Tracked as |
|---|---|---|---|
| `python-jose` and three other pinned dependencies have known CVEs. | `requirements.txt` | Swapping the JWT library is a code change with test-coverage implications, not a drop-in fix; needs its own focused task with full regression testing, not a change made incidentally during a documentation-heavy sprint. | `docs/TechnicalDebt.md` TD-011, `docs/RiskRegister.md` RS-05 |
| `orion_kernel` has exactly one consumer; some function signatures (e.g. `make_settings_getter`, `build_health_router`) are guesses at what a second product would need. | `platform/kernel/orion_kernel/*` | Cannot be validated without a real second consumer; changing it speculatively risks the "premature sharing" complexity this restructure was meant to avoid (`governance/ARCHITECTURE_PRINCIPLES.md` #7). | `docs/TechnicalDebt.md` TD-001 |
| `TokenPayload` schema in `app/schemas/user.py` is defined but not referenced anywhere in the codebase. | `app/schemas/user.py` | Low-risk either way, but it documents the JWT payload's intended shape (`sub`, `type`, `exp`) as a type contract, which has value even unused; removing it saves nothing meaningful. Left in place deliberately rather than churned. | Noted here, no register entry needed |
| Async engine `pool_size=5` (in `orion_kernel.config.OrionBaseSettings`) is a reasonable default for local single-user development but has not been load-tested. | `platform/kernel/orion_kernel/config.py` | No load-testing infrastructure exists yet; premature to tune a number with no measurement behind it. | Noted as a Sprint 2+ scaling consideration in `docs/SPRINT-2-IMPLEMENTATION-PLAN.md` |

## Checked and found clean

- **Naming:** no generic dumping-ground names (`utils`, `helpers`,
  `misc`, `common`) remain anywhere in the tree after removing the empty
  `app/utils/`. Module names describe responsibility (`security.py`,
  `database.py`, `health.py`).
- **Layer violations:** verified mechanically, not just by inspection --
  `scripts/metrics/collect_metrics.py`'s `architecture_compliance` check
  greps every file in `platform/kernel/orion_kernel` for `from app` /
  `import app` and found zero matches. The kernel never depends on
  product code; dependency direction is one-way as intended.
- **Debug artifacts:** no `print()` statements, bare `except:` clauses,
  wildcard imports, or `TODO`/`FIXME`/`XXX` comments anywhere in
  `app/` or `orion_kernel/` (checked with targeted greps across the full
  tree).
- **Unnecessary complexity:** cyclomatic complexity baseline (see
  `docs/METRICS.md`) averages 1.8 across 46 functions with a max of 8 --
  no function is doing too much.

## Verification

After the two direct fixes above, `py_compile` was re-run on the changed
files and the full pytest suite (12 tests) was re-run and passed
unchanged, confirming the cleanup introduced no regressions.
