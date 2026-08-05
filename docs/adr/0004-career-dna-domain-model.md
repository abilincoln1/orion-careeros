# ADR 0004: Career DNA Domain Model Architecture

## Status
Accepted (retroactively documented -- see "Note on timing" below)

## Note on timing
This ADR was written during Sprint 1.6 (Candidate Acceptance Review),
after the Career DNA implementation already existed in the repository.
It documents decisions that were genuinely made during implementation --
each is cross-referenced against `docs/CAREER_DNA_MODEL_SPEC.md` and
`docs/SPRINT-2-ARCHITECTURE-REVIEW.md`, both of which predate this ADR
and contain the original reasoning -- rather than inventing justification
after the fact. Per `docs/Sprint1.5-Reconciliation-Report`, writing this
ADR is one of the conditions attached to formally accepting this code as
the Sprint 2 baseline.

## Problem
CareerOS needed a data model capable of representing a person's career
history, skills, and supporting evidence in enough structural detail to
support future AI-driven reasoning (matching, recommendations, gap
analysis) without those future consumers requiring a schema redesign.
The originally-drafted Sprint 2 plan (`docs/SPRINT-2-IMPLEMENTATION-PLAN.md`)
scoped a minimal 4-table model (Skill, Experience, Project, Technology).
The model actually implemented is substantially larger and structurally
different. This ADR records why.

## Decisions

### 1. `Person` is a distinct entity from `User`
`User` (Sprint 1) is an authentication identity: email, password hash,
active/superuser flags. `Person` (Career DNA) is a career-domain profile:
name, headline, preferences. They are linked by a foreign key
(`Person.user_id -> User.id`), not merged into one table.

**Alternative considered:** add career fields directly onto `User`.
**Rejected because:** it conflates two different lifecycles and
concerns -- authentication concerns (security, session management)
should not share a table with domain concerns (name changes, profile
visibility, career preferences). It also forward-compatibly supports a
future (currently out-of-scope) case where one `User` might manage
multiple `Person` profiles (e.g. a career coach), which a merged table
would foreclose entirely. This is a constraint relaxation on the
existing FK later, not a schema redirection.

### 2. `Employment`/`Role` replaces the originally-planned flat `Experience` table
Employment history is modeled as `Employer` (deduplicated taxonomy) +
`Employment` (a person's tenure at an employer) rather than a single
denormalized `Experience` row per job.

**Alternative considered:** the original plan's flat `Experience` table
with employer name as a plain string field.
**Rejected because:** a plain string employer field cannot be
deduplicated, searched, or later enriched (e.g. company size, industry)
without a schema change; `Employer` as its own taxonomy entity solves
this once. Additionally, career changes (promotions, title changes) need
a way to represent progression at the same employer without destroying
history -- see Decision 3.

### 3. Promotions are always a new chained `Employment` row, never an in-place edit
A role change at the same employer creates a **new** `Employment` row,
linked to its predecessor via `previous_employment_id`, with the prior
row closed out (`is_current = false`, `end_date` set). The dedicated
`POST /employments/{id}/promote` endpoint is the only code path that
performs this; `PATCH /employments/{id}` explicitly cannot edit
`role_title_raw` (see `EmploymentUpdate` schema, which omits it).

**Alternative considered:** allow `role_title`/`role_id` to be edited
in-place on the existing `Employment` row.
**Rejected because:** this was the independent architecture review's
must-fix #1 (`docs/SPRINT-2-ARCHITECTURE-REVIEW.md`) -- an in-place edit
silently overwrites history, contradicting the model's own Principle 3
("history is preserved, not overwritten"). Verified via a real executed
test during Sprint 1.6 (`test_promote_creates_new_chained_row_not_in_place_edit`)
that the original row's title is provably unchanged after a promotion.

### 4. `Competency` sits above `Skill` as a distinct, composed abstraction
`Skill` is atomic and machine-matchable (e.g. "Python"). `Competency` is
composed and narrative (e.g. "Backend System Design"), linked to
supporting `Skill`s via `CompetencySkill`.

**Alternative considered:** a single unified `Skill` table with a
self-referential "is-composed-of" relationship.
**Rejected because:** `Skill` and `Competency` have different query
patterns (atomic matching vs. narrative composition) and different
future consumers (a Matching Engine wants atomic `Skill`s; a resume/
narrative generator wants `Competency`-level framing). Kept as two
tables per the architecture review's note distinguishing them, to avoid
the two concepts silently drifting into accidental duplication.

### 5. `Evidence`/`EvidenceLink` is a generic, polymorphic attachment model
`Evidence` (a URL, document, testimonial, metric, or media item) attaches
to any of nine subject types (`PersonSkill`, `PersonCompetency`,
`PersonTechnology`, `Certification`, `Education`, `Project`, `Achievement`,
`Publication`, `Reference`) via `EvidenceLink.subject_type` +
`subject_id`, a polymorphic (non-FK) reference.

**Alternative considered:** a dedicated evidence table per subject type
(`SkillEvidence`, `ProjectEvidence`, ...).
**Rejected because:** the generic model means a new evidence-bearing
entity added in a future sprint needs one new enum value, not a schema
migration to `Evidence` itself -- the explicit extension-point design
goal recorded in `docs/SPRINT-2-ARCHITECTURE-REVIEW.md`.

**Known trade-off, accepted deliberately:** because `subject_id` is not
a real foreign key, nothing at the database level cleans up orphaned
`EvidenceLink` rows when their subject is deleted. This is handled at
the service layer instead: every service that can delete an
evidence-bearing subject calls `delete_evidence_links_for_subject` in
the same transaction (architecture review must-fix #2). This is an
explicit, named, tested rule (`test_delete_person_skill_cleans_up_dependent_evidence_links`),
not an oversight.

### 6. `attribution_source` (self_reported / inferred / verified) is a derived value, never client-settable
The Create/Update API schemas for `PersonSkill`/`PersonCompetency`/
`PersonTechnology` do not expose `attribution_source` as an input field
at all. It starts at `self_reported` and is the sole responsibility of
`evidence_service._recompute_attribution`, which sets it to `verified`
when a qualifying `EvidenceLink` exists and demotes it back to
`inferred` (never back to `self_reported`) when the last such link is
removed.

**Alternative considered:** accept `attribution_source` as a client
input field, validated server-side ("must have evidence to claim
verified").
**Rejected because:** this was architecture review must-fix #5 -- any
future direct write path (bulk import, admin tool, a bug) could bypass a
service-layer-only check and produce an unverified "verified" claim,
defeating the model's central evidence-backed premise. Removing the
field from the API surface entirely means there is no code path that can
set `verified` without evidence, because there is no code path that sets
it directly. Verified via real executed tests during Sprint 1.6
(`test_attribution_source_not_client_settable`,
`test_link_evidence_promotes_attribution_to_verified`,
`test_unlink_demotes_verified_back_to_inferred`,
`test_delete_evidence_cascades_and_demotes_dependent_skill`).

### 7. Taxonomy deduplication is enforced by a database-level unique index + upsert, not service-layer lookup
`Employer`, `Role`, `Skill`, `Competency`, and `Technology` names are
deduplicated via a unique index on each entity's `normalized_name` (or
`normalized_title`) column, combined with an `INSERT ... ON CONFLICT ...
RETURNING`-style upsert at creation time (`app/repositories/taxonomy.py`).

**Alternative considered:** service-layer "look up normalized name,
insert if not found."
**Rejected because:** this was architecture review must-fix #3 -- a
textbook race condition under concurrent requests, which the database
resolves reliably and application code cannot. Verified via a real
executed test (`test_skill_taxonomy_deduplicated_across_persons`)
confirming two different users adding the same skill (in different
casing) resolve to one taxonomy row.

## Consequences

- The implemented model is a superset of, and structurally different
  from, the originally-planned 4-entity Sprint 2 scope. Any documentation
  or planning artifact referencing the original 4-table plan
  (`docs/SPRINT-2-IMPLEMENTATION-PLAN.md`, the relevant section of
  `docs/ARCHITECTURE.md`) is superseded by this ADR and
  `docs/CAREER_DNA_MODEL_SPEC.md` going forward.
- The polymorphic `EvidenceLink.subject_id` (Decision 5) requires
  service-layer discipline (every deletion path must remember to call
  `delete_evidence_links_for_subject`) that a real foreign key would
  have enforced automatically. This is accepted as a deliberate
  trade-off, not an oversight, but is a standing maintenance risk for
  any future service added to the subject-type list -- new entities
  added to `EvidenceSubjectType` must implement this cleanup call, and
  nothing currently makes forgetting to do so fail loudly at the
  database level.
- SQLite (used for the fast local/CI-less test path) does not enforce
  `ON DELETE CASCADE` foreign keys unless `PRAGMA foreign_keys = ON` is
  set per connection. This was not being set prior to Sprint 1.6, which
  meant the entire cascade-delete behavior across the schema (Person's
  and Evidence's `ondelete="CASCADE"` relationships) was silently
  untested -- a real defect this ADR's review surfaced and
  `tests/conftest.py` now fixes. See Sprint 1.6 Test Completion Report.

## Related documents
- `docs/CAREER_DNA_MODEL_SPEC.md` -- the full entity/relationship
  specification this ADR summarizes the key decisions from.
- `docs/SPRINT-2-ARCHITECTURE-REVIEW.md` -- the independent review that
  found must-fixes #1, #2, #3, #5 referenced above.
- `docs/Sprint1.5-Reconciliation-Report` -- the governance reconciliation
  that identified this ADR was missing and required it as a condition of
  acceptance.
