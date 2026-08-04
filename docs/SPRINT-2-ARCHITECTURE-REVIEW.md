# Sprint 2 Architecture Review Report

**To:** Chief Solutions Architect
**From:** Claude, Chief Software Engineer, Project ORION
**Date:** 2026-08-04
**Re:** Phase 1, Task 3 of the "Sprint 2 -- Career DNA Service" directive.
Reviews `docs/CAREER_DNA_MODEL_SPEC.md` (the proposed Career Knowledge
Model) before any Phase 2 implementation begins, per the directive's
explicit gate: "Only after this review may implementation begin."

## How this review was done
Given the directive's own framing -- "the quality of the Career Knowledge
Model will determine the quality of every future feature," "this is the
most important architectural sprint" -- a single self-review was judged
insufficient. Two passes were done instead:

1. **Self-review** during drafting: every entity's normalization,
   ownership, lifecycle, and versioning was decided deliberately, not
   defaulted, and documented inline in the spec as each decision was
   made.
2. **Independent review**, done by a fresh reviewer with no memory of
   the drafting process or its rationale -- given only the finished spec
   and the directive's own review criteria (duplication, ambiguity,
   over/under-normalization, scalability, extension points, SaaS
   implications) and asked to find real problems, not confirm the draft.
   This is the same principle behind this project's insistence on actual
   command output over claimed correctness (`governance/DEFINITION_OF_DONE.md`),
   applied to a design document instead of code.

The independent review found five real, must-fix issues that the
self-review had not caught -- proof the second pass earned its cost.
Every one has been fixed in `docs/CAREER_DNA_MODEL_SPEC.md` directly (not
just noted here); this report records what was found and why the fix is
correct, so the reasoning survives even though the spec document itself
now just shows the corrected version.

## Findings and resolutions

### Must-fix (all resolved in the spec before this report was written)

| # | Finding | Resolution |
|---|---|---|
| 1 | `Role`'s original text allowed a promotion to be recorded as *either* a new `Employment` row *or* an in-place edit of `role_id`/`role_title_raw` on the existing one -- the in-place option silently overwrites history, directly contradicting the spec's own Principle 3 ("history is preserved, not overwritten"). | Mandated: a role change at the same employer is **always** a new `Employment` row, linked to its predecessor via a new `previous_employment_id` field, forming a traceable chain. In-place edits of `role_id`/`role_title_raw` are now reserved strictly for correcting data-entry mistakes. |
| 2 | Polymorphic references (`EvidenceLink.subject_id`, `PortfolioItem.linked_entity_id`) aren't real foreign keys, so deleting a subject row (a `Project`, `Achievement`, etc.) would silently orphan any `EvidenceLink`/`PortfolioItem` rows pointing at it -- no rule required cleanup. | Added an explicit, named rule: the service layer must delete all dependent `EvidenceLink`/`PortfolioItem` rows in the same transaction as deleting their subject. Documented once in §6.3, referenced from §5.4. |
| 3 | Taxonomy dedup (`Employer`, `Role`, `Skill`, `Competency`, `Technology`) was specified as a service-layer "look up `normalized_name`, insert if not found" -- a textbook race condition under concurrent requests, producing duplicate, silently-diverging taxonomy rows. | Added a DB-level unique index on every `normalized_name`/`normalized_title` column, and changed the create path to an upsert (`INSERT ... ON CONFLICT ... RETURNING`) so the database resolves the race, not application code. |
| 4 | `EvidenceLink.subject_type` omitted `education` with no stated reason -- an oversight (every other omission in the spec is explicitly justified; this one wasn't), leaving diplomas/transcripts with no evidence-attachment path despite Credentials being a directive-named group. | Added `education` to the enum. |
| 5 | `attribution_source = 'verified'` (on `PersonSkill`/`PersonCompetency`/`PersonTechnology`) was client-settable, backed only by a service-layer "must have evidence" check with no database enforcement -- any future direct write path (bulk import, admin tool, a bug) could produce unverified "verified" claims, defeating the model's central "evidence-backed, not adjectives" premise. | Redefined `verified` as a **derived value**: the CRUD API never accepts it as client input at all (only `self_reported`/`inferred` are client-settable); the service layer computes `verified` automatically from the presence of a qualifying `EvidenceLink`. There is no code path that can set `verified` without evidence, because there is no code path that sets it directly. |

### Worth fixing, applied (not launch-blocking, but cheap and correct to do now)

- `Employment.is_current` "at most one primary current employment" rule
  upgraded from service-layer-only to a real partial unique index.
- `Reference.evidence_id` (a direct FK, inconsistent with every other
  evidence-bearing entity going through `EvidenceLink`, and silently
  capping a reference at one piece of evidence) removed; `Reference` now
  goes through `EvidenceLink` like everything else, and `reference` was
  added to `EvidenceLink.subject_type`.
- Added a one-line forward note under §8 (Taxonomy) that global taxonomy
  namespacing is additive-compatible with a future tenant-scoped
  extension, not a redesign risk -- multi-tenancy is out of scope this
  sprint, but a reviewer should not have to rediscover this later.
- Added a one-line note distinguishing `Skill` (atomic, machine-matchable)
  from `Competency` (composed, narrative) for future matching/
  recommendation consumers, since the two are structurally near-identical
  by design and that similarity could otherwise read as accidental
  duplication.

### Confirmed sound, no change (the independent review's "false alarm" findings, included for completeness)

- **Technology unifying Framework/Tool/Programming Language** behind a
  `category` discriminator: correct call. Four near-identical tables
  would have added join/CRUD/dedup surface with no behavioral
  difference.
- **Qualification as a conceptual (non-physical) supertype of Education +
  Certification**: correct call. A physical supertype table would force
  every query touching either concrete type through an extra join for a
  distinction ("is this a degree or a certification?") the `degree_level`
  vs. dedicated-table split already answers.
- **`Person` separated from `User`, with the FK living on `Person`**:
  correct forward-compatible design -- if a future (out-of-scope) phase
  needs one `User` to manage multiple `Person`s (e.g. a career coach),
  that's a constraint relaxation on the existing FK, not a schema
  redirection.
- **`Certification.expiry_date`-computed-not-stored status**: correct --
  avoids a boolean silently drifting from the date it should track.
- **`CareerProfileSnapshot` as the sole explicit full-versioning
  mechanism, with everything else's history covered by the
  fact-entity-in-place-update pattern**: defensible, not a scope dodge --
  it's targeted at the one entity with a stated future consumer ("show
  how this person's profile grew over time"), and the deferral of
  general audit-log versioning is tracked as technical debt (TD-013), not
  silently dropped.

## Scalability, extension points, and SaaS implications
- **Scalability:** the model's heaviest read pattern will be "assemble
  one person's full Career DNA" (profile + employments + skills +
  evidence, etc.) -- every Person-owned table is indexed on `person_id`
  by construction (FK + implicit index), so this is a bounded set of
  indexed lookups, not a scan, even at scale. The taxonomy tables
  (`Skill`, `Technology`, etc.) are read-heavy/write-light by nature
  (created once, referenced often) and now have real unique indexes
  (fix #3) instead of relying on race-prone application logic.
- **Extension points:** `Evidence`/`EvidenceLink`'s generic
  `subject_type` enum is the main deliberate extension point -- a new
  evidence-bearing entity added in a future sprint needs one enum value
  added, not a schema migration to `Evidence` itself. `PortfolioItem`
  follows the same narrower pattern for work-product curation.
- **SaaS implications:** covered inline in the spec (§8's new forward
  note); no redesign risk identified for the explicitly-out-of-scope
  multi-tenancy case, beyond the additive tenant-scoping extension
  already noted.

## Conclusion
Five real must-fix issues were found and resolved; the corrected spec in
`docs/CAREER_DNA_MODEL_SPEC.md` is the version this review approves for
implementation. Per the directive's own gate ("only after this review may
implementation begin"), Phase 2 (schema, migrations, services, API,
tests) proceeds on the basis of the *corrected* model documented above,
not the original draft.
