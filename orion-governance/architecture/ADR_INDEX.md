# Architecture Decision Record Index

Canonical list of all ADRs. ADRs live in `docs/adr/`. Every entry here
must exist as a file; every file in `docs/adr/` must be listed here.
Update this index in the same change that adds or supersedes an ADR.

| ID | Title | Status | Date | Summary |
|---|---|---|---|---|
| [0001](../docs/adr/0001-sprint1-foundation-stack.md) | Sprint 1 Foundation Technology Choices | Accepted | 2026-08-03 | FastAPI + SQLAlchemy 2.0 async + PostgreSQL + Alembic + JWT auth, Docker Compose, no cloud dependency. |
| [0002](../docs/adr/0002-orion-platform-restructure.md) | Introduce the ORION Platform Architecture (Kernel + Products) | Accepted | 2026-08-03 | Extracted `orion_kernel` shared package under `/platform/kernel`; restructured repo into `/platform` + `/products/careeros`; CareerOS's `app/core/*` rewritten as thin kernel bindings. |
| [0003](../docs/adr/0003-docker-naming-and-multi-project-isolation.md) | Docker Naming, Multi-Project Isolation, and Platform Kernel Distribution | Accepted (naming) / Deferred (kernel distribution) | 2026-08-04 | Adopted `orion-<product>-*` naming + configurable host ports so multiple ORION products (and unrelated projects like NDIP) can run side by side without collisions. Documented that `orion_kernel`'s current relative-path install only works for same-repository products, not a genuinely separate repository (e.g. NDIP) -- fix identified (git-based pip dependency) but explicitly not implemented yet. |
| [0004](../docs/adr/0004-career-dna-domain-model.md) | Career DNA Domain Model Architecture | Accepted (retroactively documented, Sprint 1.6) | 2026-08-05 | Documents 7 key decisions in the implemented Career DNA schema (Person vs User, Employment/Role vs flat Experience, promotion chaining, Competency abstraction, polymorphic Evidence, derived attribution_source, DB-level taxonomy dedup), each cross-referenced against `docs/CAREER_DNA_MODEL_SPEC.md` and the independent architecture review's must-fix list. Written as a Sprint 1.6 acceptance condition after the Sprint 1.5 Reconciliation Report found no ADR existed for this architecture despite it already being implemented. |
| [0005](../docs/adr/0005-sprint3-foundational-decisions.md) | Sprint 3 Foundational Decisions -- File Storage, Scheduling, AI Attribution, Job Listing Lifecycle, Repository Structure | Accepted | 2026-08-05 | Records five Chief Architect decisions resolving Sprint 3's design-phase open questions: CareerOS-local File Storage adapter (not a Platform capability yet); Scheduling built as a Platform capability; a new, explicit `AttributionSource` provenance model distinguishing user-entered/AI-extracted/imported/verified data; soft-deletion for `JobListing`; and deferral of the `/shared` repository restructure (TD-018, closed). |

## Process

New ADRs are numbered sequentially and never renumbered, even if later
superseded. A superseded ADR's Status changes to `Superseded by 000X` but
the file is not deleted. See `ARCHITECTURE_REVIEW_PROCESS.md` for when a
change requires a new ADR versus a routine code change.
