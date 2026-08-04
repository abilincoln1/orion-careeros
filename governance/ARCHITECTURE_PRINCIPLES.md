# Architecture Principles

Operational principles that translate the Engineering Constitution into
concrete design decisions. Where the Constitution says *what* must be
true, this document says *how* the codebase achieves it.

## 1. Platform / Product separation
`/platform` contains only product-agnostic code (`kernel`) and reserved
locations for future shared code (`shared_services`, `shared_libraries`,
`shared_connectors`). `/products/<name>` contains everything specific to
one product. A file that mentions CareerOS, salary bands, or job postings
by name does not belong in `/platform`.

## 2. Kernel capabilities are consumed, not copied
A product needing configuration, logging, auth primitives, database
wiring, or health endpoints imports `orion_kernel` and binds it to its own
settings/models. It does not paste kernel logic into its own tree. If a
kernel module doesn't fit a product's need, the kernel module is extended
(with a parameter, not a fork).

## 3. Knowledge graph over documents
Domain data is modeled as structured, related entities (Candidate, Skill,
Experience, Employer, Recruiter, Company, Application, Interview,
Learning Goal, Career Policy for CareerOS) with real foreign keys and
migrations -- never as opaque JSON blobs or documents standing in for a
data model.

## 4. Every capability is an API
Business logic lives behind a versioned REST endpoint
(`/api/v1/...`), documented via OpenAPI. Frontends and any future
integration call the API; they do not import backend internals.

## 5. Config over constants
If a value could plausibly differ between environments, users, or
products, it is a setting (environment variable, product Settings field,
or documented YAML config), not a literal in the code.

## 6. Small, reversible steps
Migrations must be reversible (`upgrade` and `downgrade` both
implemented and tested). Architecture changes are recorded as ADRs before
being treated as settled, so a later sprint can understand why a decision
was made and reconsider it explicitly rather than accidentally.

## 7. Deferred is not absent
Documenting a capability's responsibility and boundary (see
`docs/platform/PLATFORM_KERNEL.md`) before building it is preferred over
silently omitting it. A reserved, empty, README-only directory is a
legitimate and intentional architectural artifact, not incomplete work.

## 8. Verification is part of the deliverable
A sprint is not complete because code was written; it is complete because
tests were run and their results recorded (see `QUALITY_GATES.md` and
`DEFINITION_OF_DONE.md`). Claimed verification that was not actually
performed is a Truth First violation applied to engineering process, not
just product content.
