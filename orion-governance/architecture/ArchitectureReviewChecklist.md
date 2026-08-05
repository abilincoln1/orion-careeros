# Architecture Review Checklist

Distilled from two real architecture reviews already performed in this
project (`docs/SPRINT-2-ARCHITECTURE-REVIEW.md` and Sprint 1.6's
Candidate Acceptance Review Phase 1) -- this is a record of what actually
found real issues, not a generic industry checklist.

## Process
1. **Self-review during drafting.** Every entity's normalization,
   ownership, lifecycle, and versioning decided deliberately and
   documented inline as each decision is made -- not defaulted.
2. **Independent review**, done by a reviewer (human or a fresh AI
   session with no memory of the drafting rationale) given only the
   finished design and this checklist, asked to find real problems, not
   confirm the draft. A single self-review is insufficient for any
   design more than one sprint will build on.
3. Every finding is classified **Must-fix** (blocks acceptance),
   **Worth fixing** (cheap and correct to do now, not launch-blocking),
   or **Confirmed sound, no change** (a "false alarm" the review
   considered and rejected -- record these too; they prove the review
   was substantive, not rubber-stamping).

## What to check

- **Ownership & ambiguous boundaries.** Every mutable entity has an
  unambiguous owner. Where two entities could reasonably own the same
  concept, the ADR must state which does and why (see ADR 0004's
  Person/User separation for the pattern).
- **History preservation.** Does any operation silently overwrite data
  that should be preserved as a new record instead (see ADR 0004
  Decision 3, the promotion-chaining fix)? "Editing in place" is
  frequently the wrong default for anything representing a real-world
  event.
- **Orphan/cascade risk.** Any polymorphic or non-FK reference needs an
  explicit, named, tested cleanup rule (see ADR 0004 Decision 5). A real
  foreign key with `ondelete=` is preferred wherever the relationship
  isn't genuinely polymorphic.
- **Race conditions in dedup/uniqueness.** "Service-layer lookup, insert
  if not found" is a race condition under concurrency. Enforce uniqueness
  at the database level (unique index + upsert), not in application code
  (see ADR 0004 Decision 7).
- **Derived vs. client-settable fields.** Any field whose correctness
  depends on an invariant (e.g. "verified" implies "has evidence") must
  not be a plain client-settable input. If the API schema doesn't expose
  it, there is no code path that can violate the invariant directly (see
  ADR 0004 Decision 6).
- **Extensibility.** Does adding a new entity of an existing kind (a new
  evidence-bearing type, a new job provider, a new taxonomy) require a
  migration to unrelated tables, or just a new enum value / new
  implementation of an existing interface?
- **Dialect portability**, if the schema will be tested against SQLite
  and run against PostgreSQL: check every partial index, cascade rule,
  and driver-specific error-message assumption against BOTH dialects
  explicitly. This project has found real bugs here twice already (TD-R08,
  TD-R09) -- do not assume "works in one dialect" means "works in both."

## Output
A review report in the shape of `docs/SPRINT-2-ARCHITECTURE-REVIEW.md`:
findings table (Must-fix / Worth fixing / Confirmed sound), a
scalability/extension-points/multi-tenancy-implications section, and an
explicit conclusion stating what version of the design is approved for
implementation.
