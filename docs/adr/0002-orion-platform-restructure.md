# ADR 0002: Introduce the ORION Platform Architecture (Kernel + Products)

## Status
Accepted

> **Amendment (see ADR 0003):** the "Consequences" section below states
> that a second product can depend on `orion-kernel` via a relative
> `pip install -e ../../../platform/kernel`. That is only true if the
> second product lives inside *this same repository*, as a sibling under
> `/products`. It does not hold for a product in a genuinely separate,
> independently-cloned repository (e.g. NDIP) -- a relative path cannot
> reach across two independent git checkouts. ADR 0003 documents this
> gap and the recommended (not yet implemented) fix. Left here unedited,
> per this project's convention of not rewriting historical decisions.

## Problem
Sprint 1 delivered CareerOS as a standalone application. Following Sprint
1's Compliance Report, the Chief Architect directed that CareerOS become
the first product on a reusable ORION Platform, so that future products
do not each reimplement authentication, configuration, logging, health
monitoring, and database wiring. The repository needed a structure that
distinguishes platform-level (product-agnostic, reusable) code from
product-level (CareerOS-specific) code, without simply renaming folders
cosmetically.

## Options considered

1. **Extract a shared `orion_kernel` package under `/platform/kernel`,
   restructure the repo into `/platform` + `/products/careeros`, and have
   CareerOS's `app/core/*` become thin bindings to the kernel.** (chosen)
2. Keep a single repo/package (`backend/app`) and rely on documentation
   alone to describe which parts are "shared" in spirit, without any code
   boundary.
3. Split into fully separate repositories (`orion-kernel` repo,
   `careeros` repo) with the kernel published as a versioned package.
4. Use Python namespace packages / a monorepo tool (e.g. Nx, Bazel,
   Poetry workspaces) for stricter dependency boundaries.

Option 2 was rejected: it satisfies the letter of "document the
platform" but not the substance -- a second product would still have to
copy-paste CareerOS's `app/core` files, and nothing would prevent
platform code from silently growing product-specific assumptions. Option
3 was rejected as premature: with exactly one product, a separate
repository and package registry adds operational overhead (versioning,
publishing, dependency pinning across repos) without a second consumer to
justify it yet -- this would itself be "unnecessary complexity" per
`governance/ARCHITECTURE_PRINCIPLES.md`. Option 4 was rejected for the
same reason: a monorepo tool's dependency-boundary enforcement is only
valuable once there are boundaries worth enforcing between multiple real
packages; today there is exactly one kernel and one product.

Option 1 gives a real, enforced code boundary (a separate installable
package, `orion-kernel`, with its own `pyproject.toml`) while staying
inside a single repository and a single `pip install -e` for local
development -- the smallest change that makes the platform/product split
real rather than aspirational.

## Decision
Adopt the structure:

```
/platform
  /kernel               -- orion_kernel Python package (pip-installable, editable)
  /shared_services      -- reserved, documented, not implemented
  /shared_libraries     -- reserved, documented, not implemented
  /shared_connectors     -- reserved, documented, not implemented
/products
  /careeros
    /backend            -- FastAPI app, depends on orion_kernel
    /frontend           -- React/TS/Vite app, unaffected (no kernel dependency)
```

`orion_kernel` contains: `config.py` (`OrionBaseSettings` + a
per-product cached-settings factory), `logging.py`, `security.py`
(password hashing, JWT), `database.py` (engine/session/get_db
construction, shared readiness check), `middleware.py` (request-context
logging), and `health.py` (health/readiness router factory).
CareerOS's `app/core/*` modules were rewritten as thin subclasses/bindings
of these, not deleted -- each still exists, at the same import paths
(`app.core.config`, `app.core.security`, etc.), so nothing outside
`app/core` had to change.

The backend's Docker build context moved from `products/careeros/backend`
to the repository root, so the Dockerfile can `COPY platform/kernel` and
`products/careeros/backend` and install the kernel as a local editable
dependency at build time. `docker-compose.yml` was updated accordingly.

## Consequences
- A second ORION product can depend on `orion-kernel` (via
  `pip install -e ../../../platform/kernel` from its own backend
  directory, mirroring CareerOS) and get identical config/logging/auth/
  database/health behavior without touching CareerOS's code.
- Docker builds for the backend now use the repository root as build
  context; anyone adding new top-level directories should update
  `.dockerignore` (moved from `products/careeros/backend/.dockerignore`
  to the repo root, where Docker actually reads it for a root-context
  build) to keep image builds fast and small.
- `orion_kernel` is currently only used by CareerOS's backend, so its
  interfaces are informed by exactly one consumer; the first real second
  consumer (a future product) may reveal that some function signatures
  need to change. This is expected and acceptable -- see
  `docs/TechnicalDebt.md`.
- The full test suite (12 tests, both against in-memory SQLite and
  against a real PostgreSQL instance) was re-run after this restructure
  and passes unchanged, confirming the refactor did not alter runtime
  behavior (see `docs/SPRINT-1-ACCEPTANCE-REPORT.md` for the verification
  record).
