# Architecture Decision Record Index

Canonical list of all ADRs. ADRs live in `docs/adr/`. Every entry here
must exist as a file; every file in `docs/adr/` must be listed here.
Update this index in the same change that adds or supersedes an ADR.

| ID | Title | Status | Date | Summary |
|---|---|---|---|---|
| [0001](../docs/adr/0001-sprint1-foundation-stack.md) | Sprint 1 Foundation Technology Choices | Accepted | 2026-08-03 | FastAPI + SQLAlchemy 2.0 async + PostgreSQL + Alembic + JWT auth, Docker Compose, no cloud dependency. |
| [0002](../docs/adr/0002-orion-platform-restructure.md) | Introduce the ORION Platform Architecture (Kernel + Products) | Accepted | 2026-08-03 | Extracted `orion_kernel` shared package under `/platform/kernel`; restructured repo into `/platform` + `/products/careeros`; CareerOS's `app/core/*` rewritten as thin kernel bindings. |
| [0003](../docs/adr/0003-docker-naming-and-multi-project-isolation.md) | Docker Naming, Multi-Project Isolation, and Platform Kernel Distribution | Accepted (naming) / Deferred (kernel distribution) | 2026-08-04 | Adopted `orion-<product>-*` naming + configurable host ports so multiple ORION products (and unrelated projects like NDIP) can run side by side without collisions. Documented that `orion_kernel`'s current relative-path install only works for same-repository products, not a genuinely separate repository (e.g. NDIP) -- fix identified (git-based pip dependency) but explicitly not implemented yet. |

## Process

New ADRs are numbered sequentially and never renumbered, even if later
superseded. A superseded ADR's Status changes to `Superseded by 000X` but
the file is not deleted. See `ARCHITECTURE_REVIEW_PROCESS.md` for when a
change requires a new ADR versus a routine code change.
