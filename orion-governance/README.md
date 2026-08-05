# ORION Governance Framework

This directory is platform-level, not product-level. It belongs to
ORION itself and provides reusable engineering governance for every
ORION product -- CareerOS is the first consumer, not the owner.

**No product may edit files here without a change that also updates
this README's changelog reasoning, and no product-specific content
belongs here.** Product-specific documentation (CareerOS's API
reference, its own architecture doc, its own domain-model spec) stays
in `products/careeros/`.

## Origin
This framework was created during Sprint 3, in direct response to
Sprint 1.5's Repository Reconciliation Report, which found the
project's governance documentation and its actual code had silently
diverged. Every standard here either formalizes a practice this project
already invented under pressure (Engineering Release Package,
Configuration Integrity Matrix) or distills a lesson from a real defect
this project found (the checklists' dialect-portability and
coverage-measurement items both cite specific bugs found in Sprint 1.6).

## Structure

- `architecture/` -- ADR template, ADR index (canonical, platform-wide),
  architecture review checklist, and the architecture principles every
  product's design must respect (kernel/product boundary, no premature
  shared-code speculation, etc.).
- `engineering/` -- Definition of Done, Quality Gates, the Engineering
  Release Package standard, and the Configuration Integrity standard.
- `governance/` -- the Engineering Constitution, sprint approval
  process, repository/coding/contribution standards.
- `risk/` -- risk management and technical debt standards, including the
  `TD-`/`TD-R` numbering convention the metrics tooling depends on.
- `templates/` -- reusable document skeletons (sprint directives,
  compliance reports, release manifests, architecture reviews).
- `checklists/` -- closure, security, performance, and release
  checklists, each grounded in a real issue this project has actually
  found, not generic industry boilerplate.

## How a product consumes this
A product's own `docs/` may reference these documents but must not copy
their content -- link, don't duplicate, so a standard only needs
updating in one place. See `products/careeros/docs/ARCHITECTURE.md` for
an example of a product-level doc that correctly defers to this
framework for anything platform-wide.

## Updating this framework
A change here affects every current and future ORION product. Per
`governance/SprintApprovalProcess.md`, changes here require the same
Chief Architect authorization as any other architectural decision, and
any change to an established convention (e.g. the `TD-`/`TD-R` numbering
rule) must update every tool that depends on it in the same change
(e.g. `scripts/metrics/collect_metrics.py`'s regex).
