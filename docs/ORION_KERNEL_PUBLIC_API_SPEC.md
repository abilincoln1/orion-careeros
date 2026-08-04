# ORION Kernel Public API Specification

**Sprint:** 2 -- Career DNA Service (Phase 1, Task 2 of the directive)
**Author:** Claude, Chief Software Engineer, Project ORION
**Date:** 2026-08-04

Documents every interface `orion_kernel` (`platform/kernel/`) exposes,
classified as **Public**, **Internal**, or **Experimental**, per the
directive. **No implementation changes were made to produce this
document** -- it describes the kernel exactly as it exists after Sprint 1
Closure. Sprint 2's Career DNA Service consumes only Public interfaces
already listed here; it adds no new kernel surface (see
`docs/SPRINT-2-ARCHITECTURE-REVIEW.md` for why no kernel change was
needed).

## Classification definitions

- **Public API** -- stable, intended for every current and future ORION
  product to depend on. Changing a Public interface's signature or
  behavior is a breaking change requiring an ADR and a version bump
  (see `docs/adr/0003-docker-naming-and-multi-project-isolation.md`
  Decision 2 for how a future product would consume the kernel across
  repositories once that's implemented).
- **Internal API** -- implementation details of a Public interface.
  Importable (Python has no true private modules), but not meant to be
  used directly by product code. Product code depending on an Internal
  interface is treated as a bug in the product, not a kernel compatibility
  promise.
- **Experimental API** -- an interface that exists and works today but
  whose shape may still change based on real second-consumer feedback
  (see `docs/TechnicalDebt.md` TD-001: the kernel currently has exactly
  one consumer). None exist yet -- noted for completeness, since the
  category is part of what this document is required to define, but
  every current kernel interface has already proven stable enough
  through Sprint 1 + Sprint 1 Closure real usage to be Public, not
  Experimental.

---

## `orion_kernel.config`

| Interface | Classification | Notes |
|---|---|---|
| `OrionBaseSettings` | **Public** | Every product subclasses this for its own `Settings`. Adding a new field here is additive/safe; removing or renaming an existing field is breaking. |
| `make_settings_getter(settings_cls)` | **Public** | Every product calls this once, at import time, to get its own cached `get_settings()`. |

## `orion_kernel.database`

| Interface | Classification | Notes |
|---|---|---|
| `make_engine(settings)` | **Public** | |
| `make_session_factory(engine)` | **Public** | |
| `make_get_db_dependency(session_factory)` | **Public** | Returns a FastAPI dependency bound to the product's own session factory. |
| `check_database_connection(session)` | **Public** | Used directly by `orion_kernel.health.build_health_router`; also usable standalone. |
| `KernelBase` | **Internal** | A convenience `DeclarativeBase` products *could* use directly, but in practice every product defines its own `Base` (see `app/core/database.py`) so its own Alembic metadata is scoped to its own schema -- documented here as available, but not the path CareerOS actually takes, and not recommended for a second product either. Kept Internal rather than removed since it costs nothing to leave and a future product might have a legitimate single-schema reason to use it. |

## `orion_kernel.health`

| Interface | Classification | Notes |
|---|---|---|
| `build_health_router(settings, get_db)` | **Public** | Every product calls this once and mounts the returned router. |
| `HealthStatus` (Pydantic model) | **Public** | Part of the response contract of `/health` and `/health/live`. |
| `ReadinessStatus` (Pydantic model) | **Public** | Part of the response contract of `/health/ready`. |

## `orion_kernel.logging`

| Interface | Classification | Notes |
|---|---|---|
| `configure_logging(settings)` | **Public** | Called once at product startup. |
| `get_logger(name)` | **Public** | Thin wrapper over `logging.getLogger`; every product/module gets its logger this way rather than calling the stdlib directly, so logging behavior stays centrally controlled. |
| `JsonFormatter` | **Internal** | Wired up by `configure_logging`; a product has no reason to instantiate this itself. |

## `orion_kernel.middleware`

| Interface | Classification | Notes |
|---|---|---|
| `RequestContextMiddleware` | **Public** | Every product adds this to its FastAPI app (`app.add_middleware(RequestContextMiddleware)`). |

## `orion_kernel.security`

| Interface | Classification | Notes |
|---|---|---|
| `hash_password(password)` | **Public** | |
| `verify_password(plain_password, hashed_password)` | **Public** | |
| `create_access_token(subject, settings)` | **Public** | |
| `create_refresh_token(subject, settings)` | **Public** | |
| `decode_token(token, settings)` | **Public** | |
| `pwd_context` (module-level `CryptContext` instance) | **Internal** | An implementation detail of `hash_password`/`verify_password`. Importing it directly would let a product bypass the kernel's password-hashing policy (e.g. its configured schemes) -- exactly the kind of platform/product boundary erosion `governance/ARCHITECTURE_PRINCIPLES.md` warns about. |
| `_create_token(...)` | **Internal** (name-enforced) | Leading underscore -- Python convention for "not part of the public interface," backing both `create_access_token` and `create_refresh_token`. |

---

## What Sprint 2 (Career DNA Service) consumes
Exclusively Public interfaces, and only ones already in use since Sprint
1: `orion_kernel.database` (via `app/core/database.py`'s existing
`Base`/`engine`/`get_db`, unchanged) and, indirectly,
`orion_kernel.config`/`logging`/`middleware`/`health`/`security` (all
already wired into `app/main.py` and `app/core/*`, unchanged). Career DNA
adds **product-level** code only (`app/models`, `app/schemas`,
`app/services`, `app/repositories`, `app/api/v1`) -- see
`docs/SPRINT-2-ARCHITECTURE-REVIEW.md`. No kernel file changes.

## Consequence for future products (NDIP or otherwise)
Everything marked **Public** above is exactly what a second product would
need if/when the cross-repository kernel distribution gap (TD-012, ADR
0003 Decision 2) is closed -- this table is effectively the contract that
distribution mechanism would need to preserve. Internal interfaces are
free to change without that same compatibility obligation.
