# ADR 0005: Sprint 3 Foundational Decisions -- File Storage, Scheduling, AI Attribution, Job Listing Lifecycle, Repository Structure

## Status
Accepted

## Problem
Sprint 3's design phase (`docs/SPRINT-3-ARCHITECTURE.md`) surfaced four
open questions that were genuine product/architecture decisions, not
engineering defaults, plus one repository-structure question (TD-018)
left unresolved from the governance migration. The Chief Architect
Directive "Sprint 3 -- Phase 6 Approval & Implementation Authorisation"
(v1.1) resolved all five. This ADR is the permanent record.

## Decisions

### 1. File Storage -- CareerOS-local adapter, not a Platform capability
**Decision:** Implement a CareerOS-local `StorageAdapter` for CV
uploads. Do not build a Platform Kernel File Storage capability at this
stage.

**Alternative considered:** implement File Storage as a Platform Kernel
capability now, ahead of its originally planned sprint (`docs/platform/
PLATFORM_KERNEL.md` lists it as reserved/not implemented).

**Rejected because:** ORION currently has exactly one production
consumer (CareerOS). A platform service should not be created until at
least two products demonstrate the same requirement -- speculative
platform engineering ahead of real reuse is exactly what
`orion-governance/architecture/ArchitecturePrinciples.md` (and TD-001,
which names this same risk for the kernel generally) warns against.

**Consequence:** the storage layer is designed behind an interface
(`StorageAdapter` -- see `docs/SPRINT-3-ARCHITECTURE.md`) specifically
so that migrating to a shared Platform File Storage service later is an
adapter swap, not a CV Intelligence rewrite.

### 2. Job Provider Scheduling -- a reusable Platform capability
**Decision:** Implement scheduling as a Platform Kernel capability, not
a CareerOS-local mechanism.

**Alternative considered:** a CareerOS-local cron-equivalent, matching
Decision 1's local-first reasoning.

**Rejected because:** recurring ingestion is fundamental infrastructure
(any future ORION product with external data sources will need the same
capability), not CareerOS-specific business logic -- the opposite
situation from File Storage, where "does a second product need this
yet?" answers differently. Building it locally would very likely mean
throwaway code once a second product needs the same capability,
unlike File Storage where a local-first implementation has a clean
adapter-swap migration path.

**Consequence:** designed as a scheduler service with provider-
independent interfaces from the start, living in `platform/kernel` or
`platform/shared_services` (exact location TBD at implementation time,
per whichever the Platform Kernel's existing structure indicates -- not
prescribed further by this ADR).

### 3. AI Attribution -- new, explicit provenance values
**Decision:** Extend `AttributionSource` with distinct values for:
user-entered, AI-extracted-from-documents, imported-from-external-
systems, and verified-manually. AI-extracted information is never
classified as `self_reported`.

**Alternative considered:** reuse the existing `self_reported` value for
CV-extracted data, treating "the user uploaded a document containing
this" as equivalent to "the user typed this."

**Rejected because:** provenance is part of the product's trust model,
not an implementation convenience. `self_reported` currently means "the
person directly asserted this" -- collapsing "AI read this off an
uploaded document" into the same value would make that guarantee false,
and any future AI reasoning over Career DNA data (matching, scoring,
recommendations) depends on knowing which of these it's actually
looking at.

**Consequence:** this touches `app/models/enums.py`'s `AttributionSource`
enum, which is Career DNA (Sprint 2) code -- despite the directive's
"use Sprint 2 as-is, no redesign" instruction for Career DNA's
structure generally. This is judged an *extension* of an existing enum
to a new, previously-unanticipated data source, not a redesign of
Career DNA's model -- consistent with how `EvidenceSubjectType` was
always expected to grow by migration as new evidence-bearing entities
are added (see ADR 0004 Decision 5). Requires its own migration when
Stage 1 implementation begins; does not require re-litigating any other
part of the Career DNA design.

### 4. Job Listing Lifecycle -- soft deletion
**Decision:** `JobListing` rows are never hard-deleted. Listings a
provider stops returning are marked expired (`is_active`/`expires_at`).

**Alternative considered:** hard delete once a provider stops returning
a listing, to bound table growth.

**Rejected because:** historical integrity is more valuable than
aggressive cleanup -- `MatchResult`, `Application`, and
`RecruiterContact` records may reference a `JobListing` long after it
expires, and a user should be able to see "here's a job I matched well
with that's since closed," not have that data silently vanish.

**Consequence:** confirmed no `ondelete="CASCADE"` from `JobListing` to
any of the above (already specified this way in the original design);
storage-growth is an accepted, monitored trade-off rather than an
unconsidered one.

### 5. `/shared` repository restructure -- deferred, not performed
**Decision:** Do not move `platform/shared_services`,
`shared_libraries`, or `shared_connectors` to a top-level `/shared`
during Sprint 3. TD-018 is closed as **Deferred by Architecture
Decision**.

**Alternative considered:** perform the move to exactly match the Sprint
3 directive's original target-structure diagram.

**Rejected because:** the current structure is internally consistent,
and the proposed change offers no identified functional benefit over
moving already-documented, not-yet-implemented placeholders. Repository
stability is preferable to cosmetic restructuring absent a real driver.

**Consequence:** revisit only if and when a second ORION product
requires broader shared libraries -- the same trigger condition already
governing `platform/kernel`'s own cross-repository distribution gap
(TD-012).

## Related documents
- `docs/SPRINT-3-ARCHITECTURE.md` -- incorporates all five decisions
  directly into the design.
- `docs/SPRINT-3-ARCHITECTURE-REVIEW.md` -- the independent Phase 6
  review performed after these decisions were resolved.
- `docs/TechnicalDebt.md` -- TD-018 closed accordingly.
- `orion-governance/architecture/ArchitecturePrinciples.md` -- the
  don't-over-generalize-speculatively principle Decisions 1 and 2 both
  reason from, in opposite directions, correctly.
