# Sprint 2 Implementation Plan -- Career DNA Service (Planning Only)

> **Superseded (added 2026-08-05, Sprint 1.6):** the "Status: NOT
> AUTHORISED" line below and this plan's 4-entity scope (Skill,
> Experience, Project, Technology) do not reflect what was actually
> built. A separate, more detailed specification
> (`docs/CAREER_DNA_MODEL_SPEC.md`) and independent architecture review
> (`docs/SPRINT-2-ARCHITECTURE-REVIEW.md`) governed the real
> implementation: 24 entities including Person, Employment/Role,
> Competency, and Evidence -- a materially different and larger design.
> That implementation has since been reviewed (Sprint 1.6 Candidate
> Acceptance Review) and accepted as the Sprint 2 baseline, with its
> architecture formally recorded in `docs/adr/0004-career-dna-domain-model.md`.
> This document's scope and status are historical only; left unedited
> below per this project's convention of not rewriting historical
> records.

**Status: NOT AUTHORISED.** This document is planning only, produced as
part of Sprint 1 Closure Task 10. No Sprint 2 code, migrations, or
business logic has been implemented. Implementation may not begin until
the Chief Architect formally authorises it, per
`governance/SPRINT_APPROVAL_PROCESS.md`.

## Proposed scope

Implement the **Career DNA Service**: the first real expansion of the
Career Knowledge Graph beyond the `users` table, per the original CareerOS
specification's Career Knowledge Graph model (Candidate, Skills,
Experience, Projects, Technologies, ...). This is the natural next step
because every downstream service specified for CareerOS (Matching Engine,
Document Generation, Analytics) reads from this data -- none of them can
be meaningfully built before it exists.

### In scope (proposed)
- New entities, each foreign-keyed to `users.id`: `Skill`, `Experience`
  (employment history), `Project`, `Technology` (with a many-to-many
  association to `Skill`/`Experience` as appropriate).
- CRUD API endpoints for each entity under `/api/v1/career-dna/...`,
  following the existing auth/health patterns (versioned, documented,
  test-covered).
- Alembic migrations for the new tables, with tested `upgrade`/`downgrade`.
- Updated Career Knowledge Graph documentation reflecting the new
  entities and their relationships.

### Explicitly out of scope (deferred further)
- Any AI/LLM-assisted extraction of Skills/Experience from uploaded
  documents (that's Document Generation Service territory, in reverse,
  and involves Truth First risk that needs its own careful design).
- Matching Engine, Job Intelligence, Recruiter Intelligence -- unchanged
  from the Sprint 1 Closure directive's exclusions.
- Authorization/RBAC (TD-002) -- Career DNA data is still single-user
  scoped; every record is implicitly owned by the authenticated user via
  foreign key, same pattern as `users` today.

## Dependencies

- **Sprint 1 Closure must be accepted first**, specifically the Docker
  Compose verification gap (TD-007/RT-01) -- Career DNA's migrations
  should be proven against the same Postgres-via-Docker path that Sprint
  1's were only proven against embedded Postgres.
- **CI (TD-006)** is strongly recommended before Sprint 2 starts, so new
  endpoints and migrations are gated automatically rather than relying on
  manual verification each time, as this session had to do.
- No new external dependency is anticipated (same FastAPI/SQLAlchemy/
  Alembic/Pydantic stack); no new Platform Kernel capability is required
  -- Career DNA is ordinary CRUD on top of existing auth/database/health
  infrastructure.

## Architecture review

- New models live in `products/careeros/backend/app/models/`, alongside
  `user.py`, each with proper foreign keys -- not JSON blobs (Career
  Knowledge Base principle).
- New endpoints live in `products/careeros/backend/app/api/v1/`, one
  router module per entity or a combined `career_dna.py`, registered in
  `app/api/v1/router.py` -- following the existing `auth.py`/`health.py`
  pattern, no new architectural pattern needed.
- No change to `/platform/kernel` is anticipated. If Career DNA reveals a
  genuine second need for a kernel capability, that is itself grounds for
  an ADR (see `governance/ARCHITECTURE_REVIEW_PROCESS.md`), not a
  reason to change the kernel preemptively now.

## Risk assessment

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Data model gets over-designed before real usage patterns are known (e.g. speculative fields for Matching Engine that doesn't exist yet) | Medium | Medium | Model only what Career DNA itself needs to represent a candidate's skills/experience/projects/technologies; defer Matching-Engine-specific fields (weights, scores) until that sprint. |
| Migration complexity grows (multiple new tables + relationships in one sprint) | Medium | Medium | Land migrations incrementally (one entity, one migration, one test pass at a time) rather than one large migration for all four entities. |
| CRUD endpoints proliferate without consistent validation/error patterns | Low | Low | Reuse the existing Pydantic schema + FastAPI dependency patterns from `auth.py`; no new pattern needed. |
| Test suite runtime grows and developers stop running it locally | Low | Low | Keep the SQLite-default / Postgres-optional test split from Sprint 1; add CI so it always runs regardless of developer habit. |

## Database impact

- Four new tables (`skills`, `experiences`, `projects`, `technologies`)
  plus at least one association table (e.g. `experience_technologies`)
  if a many-to-many relationship is modeled, as the original
  specification implies ("Model relationships between... Skills,
  Experience, Projects, Technologies").
- All new tables foreign-key to `users.id`; no changes to the existing
  `users` table are anticipated.
- Estimated migration count: 4-6 (can be landed as one migration per
  entity for reversibility and reviewability, per
  `governance/DEFINITION_OF_DONE.md`).

## Estimated effort

Rough sizing, not a committed estimate (no team velocity data exists yet
for this project):

| Work item | Estimate |
|---|---|
| Models + migrations (4 entities + associations) | 1-2 sessions |
| CRUD API endpoints + schemas | 1-2 sessions |
| Tests (unit + API, SQLite and Postgres-parity) | 1 session |
| Documentation (ARCHITECTURE.md, API.md updates, ADR if the data model needs one) | 0.5 session |
| Verification (Docker end-to-end, if TD-007 is by then resolved) | 0.5 session |

## Acceptance criteria

1. All four entities exist as SQLAlchemy models with working, reversible
   Alembic migrations, verified against real PostgreSQL (not just
   SQLite), continuing the Sprint 1 Closure precedent.
2. CRUD endpoints for each entity exist under `/api/v1/career-dna/...`,
   documented via OpenAPI, and require authentication (only the owning
   user can read/write their own Career DNA records).
3. Unit + API test coverage matches or exceeds the current 83.42%
   baseline (`docs/METRICS.md`).
4. `docs/ARCHITECTURE.md` and `docs/API.md` updated in the same change
   (per `governance/DEFINITION_OF_DONE.md` #5).
5. `docs/metrics.json` regenerated and compared against the Sprint 1
   Closure baseline; any regression (e.g. complexity spike, coverage
   drop) is explained, not silently accepted.
6. No business logic beyond CRUD + ownership scoping -- no scoring,
   matching, or AI-assisted extraction sneaks into this sprint.

## Success metrics

- Test suite remains green (SQLite and Postgres) with the new entities
  included.
- Code coverage does not regress below the Sprint 1 Closure baseline.
- Cyclomatic complexity average does not meaningfully increase (CRUD
  endpoints are inherently low-complexity; a spike would indicate scope
  creep into business logic).
- Technical debt register gains no more than a small, explicitly-reasoned
  number of new entries (some is expected and healthy; an unexplained
  large increase indicates rushed work).

## Sprint backlog (proposed, for Chief Architect approval)

1. ADR (if needed): confirm the Career Knowledge Graph's exact
   entity/relationship shape before writing migrations.
2. `Skill` model + migration + tests.
3. `Technology` model + migration + tests.
4. `Experience` model + migration + tests (references `Technology`
   many-to-many if modeled that way).
5. `Project` model + migration + tests (references `Technology`).
6. CRUD API endpoints for all four entities, ownership-scoped to the
   authenticated user.
7. Documentation updates (ARCHITECTURE.md, API.md, metrics re-run).
8. Sprint 2 acceptance report, in the same format as
   `docs/SPRINT-1-ACCEPTANCE-REPORT.md`.

Authorization to execute this backlog is requested from the Chief
Architect separately from this planning document, per
`governance/SPRINT_APPROVAL_PROCESS.md`.
