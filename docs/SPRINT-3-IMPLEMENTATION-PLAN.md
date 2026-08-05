# Sprint 3 Implementation Plan -- Job Intelligence Platform (Planning Only)

**Status: NOT AUTHORISED FOR IMPLEMENTATION.** Per the Sprint 3
directive: "Do not begin Sprint 3 feature implementation until the
architecture, governance migration, and design deliverables have been
completed and approved." This document is the planning artefact that
becomes actionable once `docs/SPRINT-3-ARCHITECTURE.md` is reviewed
(Phase 6) and the four open questions in that document's Section 7 are
resolved by the Chief Architect.

## Proposed sequencing
Each component below is independently implementable once its design is
approved, but this order minimizes rework: later components depend on
earlier ones' actual (not just designed) schemas.

1. **Document Intelligence Engine** -- no dependency on Job Intelligence; can start
   first once Open Question 1 (file storage) and Open Question 3
   (attribution_source) are resolved.
2. **Job Intelligence** -- provider interface + at least one real
   provider implementation (recommend starting with whichever provider
   has the simplest official API, to validate the interface before a
   second provider is added); depends on Open Question 2 (scheduling).
3. **Matching Engine** -- depends on both 1 and 2 having real data to
   score against; implement scoring dimension-by-dimension (start with
   Skills, the dimension with the clearest existing data model), not
   all seven dimensions simultaneously.
4. **Recruiter Watchlist** -- independent of 1-3; could be reordered
   earlier if useful as a lower-risk first Sprint 3 increment.
5. **Interview Pipeline** -- benefits from Job Intelligence/Recruiter
   Watchlist existing (for the nullable FKs) but is not blocked by them.

## Per-component backlog shape
Each component's backlog should follow the same pattern Sprint 2
validated: model + migration + tests, one entity at a time, not one
combined migration -- see `orion-governance/architecture/
ArchitectureReviewChecklist.md` and `orion-governance/engineering/
DefinitionOfDone.md`.

## Explicitly out of scope for Sprint 3 implementation
- Any actual scraping or automation outside a provider's terms of
  service (Job Intelligence Section 3's hard constraint).
- Automated recruiter outreach (Recruiter Watchlist is a CRM, not an
  automation tool, per the directive).
- Company Intelligence as its own service (the `Company` entity
  referenced by `JobListing.company_id` is a nullable placeholder FK
  only -- implementing Company Intelligence itself is a future,
  separately-authorized sprint).
- RBAC/multi-tenancy (still tracked as TD-002, unchanged by this sprint).

## Dependencies
- Career DNA (`v0.2.0-sprint2`) -- satisfied.
- The two Platform Kernel `shared_services` capabilities named in Open
  Questions 1 and 2 (File Storage, Scheduling) -- **not yet
  implemented**; Sprint 3 implementation cannot fully proceed without a
  decision on each (build now vs. interim shim).
- CI (TD-006) -- still not implemented; recommended before Sprint 3
  implementation begins, for the same reason it was recommended before
  Sprint 2 (manual verification does not scale to 5 new services).

## Acceptance criteria (per component, mirroring Sprint 2's proven shape)
1. Models + reversible Alembic migrations, verified against real
   PostgreSQL, not just SQLite -- and explicitly re-verified for
   `PRAGMA foreign_keys`-equivalent correctness given TD-R08's lesson.
2. CRUD/read endpoints where applicable, documented, authenticated,
   ownership-scoped.
3. Test coverage matching or exceeding the current 96.01% baseline,
   measured with the corrected `.coveragerc` configuration from the
   start (not discovered as a gap after the fact, per TD-R11's lesson).
4. Documentation (ARCHITECTURE.md, API.md) updated in the same change.
5. `docs/metrics.json` regenerated and compared against the Sprint 2
   baseline.
6. No business logic beyond what each component's design specifies --
   no scope creep into a neighboring component's stated ownership
   (Section 4 of the architecture doc).

## Sprint backlog (proposed, for Chief Architect approval)
1. Resolve Open Questions 1-4 in `docs/SPRINT-3-ARCHITECTURE.md`.
2. Phase 6 independent architecture review (per the directive) --
   produces a `SPRINT-3-ARCHITECTURE-REVIEW.md` in the same shape as
   `docs/SPRINT-2-ARCHITECTURE-REVIEW.md`.
3. Document Intelligence Engine: `Document` + `DocumentExtractionRun` models/migrations/
   tests, extraction service, integration with existing Career DNA
   write paths.
4. Job Intelligence: `JobProvider`/`JobListing`/association models,
   Provider Interface implementation, first real provider.
5. Matching Engine: `MatchResult`/`MatchScoreComponent` models,
   dimension-by-dimension scoring, starting with Skills.
6. Recruiter Watchlist: `Recruiter`/`Agency`/`RecruiterContact` models,
   CRUD endpoints.
7. Interview Pipeline: `Application`/`InterviewEvent` models, status
   workflow, dashboard/reporting endpoints.
8. Sprint 3 acceptance report + Engineering Release Package, per
   `orion-governance/engineering/EngineeringReleasePackageStandard.md`.

Authorization to execute this backlog is requested from the Chief
Architect separately from this planning document, per
`orion-governance/governance/SprintApprovalProcess.md`.
