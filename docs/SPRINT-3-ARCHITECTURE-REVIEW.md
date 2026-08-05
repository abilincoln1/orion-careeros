# Sprint 3 Job Intelligence Platform -- Independent Architecture Review Report

**To:** Chief Solutions Architect (ChatGPT), ORION Architecture Review Board
**From:** Claude (Anthropic), acting as independent reviewer
**Date:** 2026-08-05
**Re:** Phase 6 of the Sprint 3 v1.1 directive -- independent review of `docs/SPRINT-3-ARCHITECTURE.md`.

## How this review was done

Per the directive's explicit instruction, this review was conducted as
if evaluating a third-party pull request: the author's own rationale
was not taken as given, each design choice was re-derived from first
principles, and the goal was to find real weaknesses, not confirm the
draft. This is the same discipline `docs/SPRINT-2-ARCHITECTURE-REVIEW.md`
established for Career DNA -- a design this consequential does not get
to pass on a single self-review.

**Caveat, stated plainly rather than glossed over:** the same AI
(Claude) that wrote the original design also performed this review, in
a fresh reading pass rather than a second independent session. This is
weaker than a genuinely separate reviewer (human or an independent AI
session with no access to the drafting conversation) and is named here
so the Chief Architect can weigh the review's findings accordingly, per
this project's Truth First principle (overstating independence would
itself be a violation of it).

## Findings and resolutions

### Must-fix (resolved directly in `docs/SPRINT-3-ARCHITECTURE.md` before this report was finalized)

| # | Finding | Resolution |
|---|---|---|
| 1 | `CVDocument.storage_ref` was a bare field with no interface behind it, despite Chief Architect Decision 1 explicitly requiring the storage layer be "designed behind an interface" so a later migration to a shared Platform capability doesn't require rewriting CV Intelligence. | Added a `StorageAdapter` protocol (`store`/`retrieve`/`delete`) with an explicit statement that Sprint 3 implements exactly one adapter (CareerOS-local), and migration later is an adapter swap. |
| 2 | `Application.status_history_json` (a JSON blob) directly contradicts this project's own established principle from ADR 0004 Decision 3 -- "history is preserved as new records, not overwritten or embedded in a mutable blob." This is the identical defect class Sprint 2's own must-fix #1 (Employment promotion chaining) corrected; using a JSON blob here would have reintroduced a defect this project already found and fixed once. | Replaced with a proper `ApplicationStatusTransition` table, with `Application.status` retained only as a denormalized current-state column, updated in the same transaction as each new transition row. |
| 3 | `ProviderFetchResult` was referenced in the `JobProviderClient` interface but never defined -- an interface with an undefined return type is not a real interface. | Defined explicitly as a dataclass with `raw_listings`, `next_cursor`, and an `is_exhausted` property. |
| 4 | The RSS-vs-API pagination question was raised as an open concern in the original design's own text but never resolved -- `fetch_listings`'s cursor semantics silently assumed API-style pagination. | Resolved explicitly: RSS providers treat the newest-processed-item's timestamp as their cursor, giving exactly one exhaustion signal (`next_cursor is None`) regardless of provider type -- callers never branch on `provider_type`. |
| 5 | `JobProvider.credentials_ref` was described only as "a pointer to a secret," with no stated resolution mechanism -- not specific enough to implement against. | Defined for Sprint 3 as an environment-variable name, resolved at request time, never persisted or logged -- the simplest mechanism satisfying the stated constraint, with a clear later migration path to a real secrets manager. |

### Worth fixing, named for Stage 1+ implementation (not blocking Phase 6 approval)

- **CV Intelligence -> Career DNA write-boundary enforcement.** The
  design states CV Intelligence may only write to Career DNA through
  existing Sprint 2 service functions, but nothing makes this
  structurally true. A stated boundary with no enforcement mechanism is
  a policy, not an architecture. Recommend an import-boundary lint rule
  or, at minimum, an explicit Definition-of-Done test for Stage 1.
- **Provider test fixtures.** No provider implementation should be
  exercised against a live external API in automated tests. A
  `MockProviderClient` against fixture data should exist before the
  first real provider is built, not retrofitted after.
- **`MatchResult`/`MatchScoreComponent` cascade from `Person`.** The
  original design specified these should NOT cascade from `JobListing`
  (correct, preserves history) but never stated their cascade behavior
  relative to `Person`. Should cascade from `Person`, consistent with
  every other Career-DNA-adjacent table -- named explicitly now rather
  than left implicit.
- **`MatchScoreComponent.explanation` as free text only.** Adequate for
  display, weak for AI-readiness (an explicit review criterion in this
  directive). Recommend pairing with a structured `reason_code` enum
  for Stage 3 -- not blocking, since free text still satisfies the
  "transparent, explainable" requirement for a human reader.

### Confirmed sound, no change (considered and rejected as false alarms)

- **`MatchScoreComponent` as its own table rather than a JSON blob on
  `MatchResult`.** Considered whether this was over-engineering for
  Sprint 3's scope. Rejected: the directive's own dashboard/reporting
  requirement ("show me everyone who matched well on skills but poorly
  on salary") needs this queryable at the database level: exactly the
  same reasoning that resolved must-fix #2 above. Keeping it a separate
  table is the design being consistent with itself, not redundant.
- **Fixed 7-value enum for `MatchScoreComponent.dimension`** rather than
  an open/configurable dimension list. Considered whether this limits
  future extensibility (an 8th matching dimension would need a
  migration). Rejected as a real problem: this mirrors Career DNA's own
  precedent (`EvidenceSubjectType`, a closed enum extended by migration
  when genuinely needed) which has caused no issues in Sprint 2. A
  closed, explicit set is more maintainable than a stringly-typed
  "dimension" column for a set of 7 values that change rarely.
- **Person/CareerProfile left completely unmodified by this sprint's
  design**, despite CV Intelligence conceptually "belonging near"
  Career DNA. Considered whether CV Intelligence needed its own
  Person-adjacent entity. Rejected: `CVDocument`/`CVExtractionRun` are
  correctly scoped as CV Intelligence's own concern, writing INTO
  Career DNA rather than extending it -- extending Career DNA itself
  here would have violated the directive's explicit "use Sprint 2
  as-is, no redesign" instruction.

## Domain and service boundary evaluation (directive's required dimensions)

- **Domain boundaries:** Clean. Five services, five distinct
  responsibilities (Section 4 of the architecture doc), no service
  reaches into another's owned tables except through defined interfaces
  or explicit read-only relationships.
- **Service boundaries:** Sound in design, weak in enforceability (see
  Worth-fixing above) -- a real but not blocking gap.
- **Provider abstraction:** Was genuinely incomplete before this
  review's must-fixes (undefined return type, unresolved pagination
  contract); now complete and internally consistent.
- **Database design:** Sound, with one real defect found and fixed
  (status-history-as-JSON) and one omission named (Person cascade on
  Match tables).
- **Kernel responsibilities vs. product responsibilities:** Correctly
  reflects the Chief Architect's Decisions 1 and 2 -- File Storage stays
  product-local, Scheduling becomes a genuine Platform capability, with
  stated rationale matching `ArchitecturePrinciples.md`'s
  don't-over-generalize-speculatively principle.
- **Future extensibility:** Provider interface and Evidence-style
  subject-type extension points are both genuine, low-cost extension
  points, consistent with Career DNA's own successful patterns.
- **Maintainability:** No red flags found beyond the items above.
- **Testability:** One real gap found (provider fixtures) -- named as a
  Stage 2 prerequisite, not retrofitted after the fact.
- **AI-readiness:** Attribution provenance now explicit and structured
  (Decision 3). Match explanation currently text-only -- a Worth-fixing
  item, not a blocker, since the requirement is human explainability
  first.

## Recommendation

# Approve with Conditions

**Conditions**, all of which are Stage-specific Definition-of-Done gates
rather than blockers to starting Stage 1:

1. Stage 1 (CV Intelligence) must implement or explicitly enforce the
   CV Intelligence -> Career DNA write-boundary (a lint rule, or at
   minimum a named test asserting no direct model import).
2. Stage 2 (Job Provider Framework) must include a `MockProviderClient`
   test fixture before the first real provider client is merged.
3. `MatchResult`/`MatchScoreComponent`'s `Person`-cascade behavior must
   be implemented as specified in this review before Stage 3 is
   considered done.

None of the five Must-fix items block approval -- they are already
resolved in the design document itself, per this project's established
convention of fixing the spec in place rather than merely describing
the fix. The design is architecturally sound, correctly scoped against
Career DNA without redesigning it, and consistent with every real
lesson this project has learned so far (history-as-rows not JSON,
dialect/interface portability, explicit provenance).
