# ORION Platform

This directory is the ORION Platform itself: the reusable engineering
foundation that every ORION product (CareerOS is the first) is built on
top of. See `docs/platform/PLATFORM_KERNEL.md` for the full list of
Platform Kernel responsibilities and which are implemented today versus
documented for future sprints, and `docs/ARCHITECTURE.md` for how this
fits together with `/products`.

## Structure

- `kernel/` -- **Implemented.** The `orion_kernel` Python package:
  configuration, logging, authentication primitives, database
  engine/session construction, health-check router, and request
  middleware. Installed by product backends as a local editable
  dependency (see `products/careeros/backend/requirements.txt`).
- `shared_services/` -- **Documented, not yet implemented.** Platform
  Kernel responsibilities that are cross-cutting *services* rather than
  importable library code (Notifications, Event Bus, Scheduling, Audit,
  Monitoring, File Storage, Document Engine, Communication Hub). See the
  README in that directory and `docs/platform/PLATFORM_KERNEL.md`.
- `shared_libraries/` -- **Reserved.** Placeholder for future
  product-agnostic libraries (e.g. a shared validation or date/currency
  utilities package) that don't yet exist because no product has needed
  them. Not to be confused with `kernel/`, which exists and is consumed
  today.
- `shared_connectors/` -- **Reserved.** Placeholder for the eventual
  connector framework (job boards, recruiter mailboxes, company data
  sources) described in the original CareerOS specification's Job
  Intelligence Framework. Explicitly out of scope until a sprint
  authorizes Job Intelligence work.

## Why a platform, not just an app

CareerOS was built first, but the Chief Architect directive following
Sprint 1 required establishing a reusable platform underneath it so that
future ORION products do not each reimplement authentication,
configuration, logging, health monitoring, and database wiring from
scratch. `kernel/` is the concrete result of that: CareerOS's own
`app/core/*` modules are now thin product-level bindings around
`orion_kernel`, not independent implementations.
