# ORION Platform Metrics Framework

`scripts/metrics/collect_metrics.py` produces a machine-readable snapshot
(`docs/metrics.json`) of the engineering metrics below. Run it at the end
of every sprint and compare against the previous baseline -- this becomes
the engineering dashboard referenced in the Chief Architect directive.
There is currently no historical trend (see `docs/TechnicalDebt.md`
TD-008); this document holds the Sprint 1 Closure baseline only.

## Running it

```bash
pip install radon pytest-cov pip-audit --break-system-packages   # dev-only tools, not app runtime deps
python3 scripts/metrics/collect_metrics.py
```

## What each metric measures and how

| Metric | Tool / method | Why it's checked this way |
|---|---|---|
| Code coverage | `pytest --cov=app` against `products/careeros/backend/app` | Line coverage of the product backend under its default (SQLite) test run. |
| Cyclomatic complexity | `radon cc -a` against `app/` and `orion_kernel/` | Average and max per-function complexity across both the product and the kernel. |
| Dependencies | Parsed from `requirements.txt` (excluding the local `-e` kernel line) and `package.json` | A direct count of what has to be tracked for upgrades/CVEs. |
| Migration count | Count of files in `alembic/versions/` | Simple proxy for schema-change velocity. |
| API count | Regex count of `@router.<method>(` across `app/` | Counts actual registered REST endpoints. |
| Docker image size | `docker image ls` after `docker compose build` | **Not measured in this environment** -- no Docker daemon available. Must be captured by the user after their first `docker compose up --build`. |
| Security findings | `pip-audit` against a frozen, `-e`-line-stripped copy of `requirements.txt` | Avoids pip-audit trying (and failing) to resolve the local editable kernel path; reflects CareerOS's actual pinned dependencies rather than the whole shared build environment. |
| Technical debt | Regex count of `TD-\d+` (open) vs `TD-R\d+` (resolved) rows in `docs/TechnicalDebt.md` | Keeps the debt count honest and mechanically derived rather than hand-maintained separately. |
| Architecture compliance | Static check: no file under `platform/kernel/orion_kernel` may contain `from app` / `import app` | A cheap, real enforcement of `governance/ARCHITECTURE_PRINCIPLES.md` principle 1 (kernel never depends on product code). |

## Sprint 1 Closure baseline (captured this session)

| Metric | Value |
|---|---|
| Code coverage | 83.76% |
| Cyclomatic complexity | average 1.77, max 7, across 47 functions/methods (both product and kernel code) |
| Dependencies | 17 backend (Python), 7 frontend (npm) |
| Migration count | 1 |
| API endpoint count | 4 (`/auth/register`, `/auth/login`, `/auth/refresh`, `/auth/me`; health endpoints are built via the kernel's router factory and counted separately -- see note below) |
| Docker image size | Not measured in this session's environment; **confirmed buildable and runnable** by the user's own `docker compose up --build` runs (see `docs/TechnicalDebt.md` TD-R07) |
| Security findings | 22 known vulnerabilities across 5 pinned packages -- see `docs/TechnicalDebt.md` TD-011 and `docs/RiskRegister.md` RS-05 |
| Technical debt | 11 open, 7 resolved (10 open / 7 resolved after Sprint 1 Closure's Docker re-verification, plus TD-012 added during the Docker Build Review / Sprint 2 Readiness audit -- see `docs/SPRINT-2-READINESS-REPORT.md`) |
| Architecture compliance | Compliant -- 0 instances of kernel code importing product code |
| Lines of code | 475 (product backend `app/`), 425 (platform kernel), 193 (tests) |

Note on API count: the regex only matches `@router.<verb>(` decorators
written directly in product code. The three health endpoints
(`/health`, `/health/live`, `/health/ready`) are registered dynamically
inside `orion_kernel.health.build_health_router`, so they don't appear as
`@router.get(...)` literals in `app/`. Counting them by hand: CareerOS
currently exposes **7** total endpoints (4 auth + 3 health). The script
undercounts kernel-provided routes by design (it's meant to measure
product-authored surface area); this is noted here rather than silently
left ambiguous.

Full raw output is in `docs/metrics.json`, regenerated each run.
