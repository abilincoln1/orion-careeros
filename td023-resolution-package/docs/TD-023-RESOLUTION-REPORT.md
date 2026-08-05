# TD-023 Resolution Report

**To:** Chief Solutions Architect
**From:** Claude, Chief Software Engineer, Project ORION
**Date:** 2026-08-06
**Re:** Resolving the Career DNA provenance gap blocking Sprint 3 Stage 1's Career DNA integration.
**Status: DESIGN ONLY. No implementation authorized. Awaiting explicit approval per the directive's Implementation Gate.**

---

## 1. Task 1 -- Full Career DNA provenance audit

Every location where provenance is written, inferred, validated, or consumed, found by direct inspection of the codebase (not from memory or assumption):

| Entity | Provenance field? | Where written | Where consumed |
|---|---|---|---|
| **Person** | None. Plain profile fields (`first_name`, `last_name`, `headline`, etc.) | `person_service.create_person`/`update_person` | Nowhere -- no concept of "verified" applies to a person's own name. |
| **PersonSkill** | `attribution_source` (`self_reported`/`inferred`/`verified`, +`ai_extracted`/`imported` per ADR 0005) | Defaults to `self_reported` in `skill_service.add_person_skill`; the ONLY other writer is `evidence_service._recompute_attribution` | `PersonSkillRead` API response; no other business logic branches on it today |
| **PersonCompetency** | Same as PersonSkill | Same pattern (not yet exercised by any built endpoint -- Competency has no CRUD API yet, only the model exists) | Same |
| **PersonTechnology** | Same as PersonSkill | Same pattern (also no CRUD API built yet) | Same |
| **Employment** | **None** | `employment_service.create_employment`/`promote_employment` | N/A |
| **Education** | **None** | No service exists yet (model only, per `docs/CAREER_DNA_MODEL_SPEC.md` -- Sprint 2 built the model, not the API) | N/A |
| **Certification** | **None** | No service exists yet (model only) | N/A |
| **Project** | **None** | No service exists yet (model only) | N/A |
| **Achievement** | **None** | No service exists yet (model only) | N/A |
| **Publication** | **None** | No service exists yet (model only) | N/A |
| **Reference** | **None** | No service exists yet (model only) | N/A |
| **Evidence** | `verified_by`/`verified_at` -- a **different** concept: who confirmed the evidence itself is genuine, not who/what asserted the fact it supports | `evidence_service.create_evidence` (both currently always `None` -- no verification workflow built yet) | Not yet consumed anywhere |
| **CareerGoal / LocationPreference / SalaryPreference / WorkPreference** | **None** | No service exists yet (model only) | N/A |

**Critical finding, not previously stated this precisely:** `evidence_service.py`'s own `_ATTRIBUTION_BEARING_TYPES` set and its inline comment confirm this was **always a deliberate Sprint 2 design choice**, not an oversight discovered only now: *"Certification/Education/Project/Achievement/Publication/Reference don't have that field at all -- evidence there is just supporting proof, not something that flips a self-reported/verified switch."* Sprint 2 intentionally scoped provenance to exactly three entities (Skill/Competency/Technology) where a self-reported-vs-verified distinction was judged to matter for the product. TD-023 is therefore not "Sprint 2 forgot this" -- it is "Sprint 2's deliberate scope doesn't yet cover what the Document Intelligence Engine needs," a materially different and more precise framing that changes which solutions are appropriate.

**Second finding:** most of the entities TD-023's original text worried about (Education, Certification, Project, Achievement, Publication, Reference) **have no service layer at all yet** -- only ORM models exist. This means TD-023 as originally scoped conflated two different gaps: (a) Employment specifically, which has a working service but no provenance field, and (b) six other entities, which have neither a provenance field nor any way to be written at all yet, by anyone, human or AI. Only (a) is a real blocker for Stage 1 today; (b) is out of scope until those services are built in a future sprint.

---

## 2. Task 2 -- Design options

### Option A: Add `attribution_source` column to every remaining entity (full symmetry)

Extend `Employment`, `Education`, `Certification`, `Project`, `Achievement`, `Publication`, `Reference` with the same `attribution_source` column pattern PersonSkill/Competency/Technology already use.

- **Advantages:** Maximum consistency; every entity answers "who/what asserted this" the same way; simplest mental model.
- **Disadvantages:** Directly reopens Sprint 2's deliberate scoping decision for six entities that don't have a service layer yet -- doing this now means designing (and reviewing) provenance semantics for entities nobody has built CRUD for, pure speculative work for five of the six (only Employment is actually blocking anything today).
- **Migration impact:** 7 new columns, 7 `ALTER TABLE ... ADD COLUMN` migrations (or one combined), plus enum type changes if `AttributionSource` itself changes (see TD-022).
- **Backward compatibility:** Additive, non-breaking for existing rows (default `self_reported`).
- **Security implications:** None beyond what PersonSkill already established.
- **Future AI implications:** Clean -- every entity type is immediately AI-extraction-ready.
- **Future human-edit implications:** A human editing an AI-extracted Employment record would need the same must-fix-#5-style protection PersonSkill has (client can't directly claim `verified`) -- work not yet designed for six new entities.
- **Future multi-provider implications:** No change needed; provenance is per-row, provider-agnostic already.

### Option B: Add `attribution_source` to Employment only, now; defer the rest

Same mechanism as Option A, but scoped to the one entity actually blocking Stage 1.

- **Advantages:** Solves the actual, present blocker with minimum surface area; doesn't speculatively design provenance semantics for entities with no service layer yet; smallest reviewable change.
- **Disadvantages:** TD-023 will recur, by name or in spirit, the moment Education/Certification/Project services are eventually built and someone wants to extract those from a CV too (which is likely, since CVs routinely list education and certifications).
- **Migration impact:** 1 new column, 1 migration.
- **Backward compatibility:** Additive, non-breaking.
- **Security implications:** None beyond PersonSkill's existing precedent.
- **Future AI implications:** Solves CVs' two most common sections (employment, skills); education/certifications remain unextractable by this engine until their own services exist anyway -- so this isn't actually a functional gap versus Option A, just a sequencing difference.
- **Future human-edit implications:** Same must-fix-#5-style protection needed for Employment, scoped to one entity instead of seven.
- **Future multi-provider implications:** Same as Option A.

### Option C: A generic, polymorphic `DataProvenance` table (mirrors the existing `EvidenceLink` pattern)

One new table: `subject_type` (enum, extensible), `subject_id` (polymorphic, not a real FK -- same trade-off `EvidenceLink` already accepted and documented as TD-013), `attribution_source`, `document_extraction_run_id` (nullable FK, linking back to exactly which AI extraction produced this, when applicable), `set_at`.

- **Advantages:** Adding provenance to a new entity type later needs zero schema migration on that entity -- just a new enum value and a service-layer read/write against the existing table. Directly reuses a pattern this project has already built, tested, and understood the trade-offs of (`EvidenceLink`). Naturally extends to the "future multi-provider implications" requirement: `document_extraction_run_id` gives a real, queryable link from "this fact" to "which extraction run, which provider, asserted it," which per-column `attribution_source` alone does not.
- **Disadvantages:** Introduces a second polymorphic-reference pattern alongside `EvidenceLink`'s, meaning TD-013's orphan-cleanup discipline (every deletion path must remember to clean up dependent rows) now applies to two tables' worth of subjects instead of one -- a real, compounding maintenance burden this project has already flagged as a known risk once.
- **Migration impact:** 1 new table, 1 migration. No changes to any existing entity's schema at all.
- **Backward compatibility:** Fully additive; existing `PersonSkill.attribution_source` etc. would need a decision (see Section 2.1 below) about whether to migrate onto the new table or coexist.
- **Security implications:** Same ownership-scoping discipline as `EvidenceLink` already requires (verified in that table's existing tests).
- **Future AI implications:** Best of the three options -- a `document_extraction_run_id` FK gives real traceability ("show me every fact this specific CV upload produced") that a bare enum column cannot.
- **Future human-edit implications:** Same must-fix-#5-style protection needed, but designed once, for the generic table, rather than per-entity.
- **Future multi-provider implications:** Best of the three -- comparing two providers' extractions of the same document becomes a query against one table, not N.

#### 2.1 A sub-question Option C raises, named explicitly rather than glossed over
If Option C is chosen, does `PersonSkill.attribution_source` (and Competency/Technology) get migrated onto the new generic table, or does it stay as a column and the codebase ends up with two provenance mechanisms side by side? Migrating it is the more consistent answer but is itself a real, reviewable Sprint-2-schema-touching change with its own migration and test risk -- not something to fold silently into "resolve TD-023."

### Option D: No new column anywhere -- rely entirely on `DocumentExtractionRun`'s existing audit trail, gate every write behind explicit per-field human confirmation

Treat "a human reviewed the AI's extraction and explicitly confirmed this specific field" as equivalent to `self_reported`, on the reasoning that the human is now the one asserting it. No schema change to any Career DNA entity.

- **Advantages:** Zero schema change; ships fastest.
- **Disadvantages:** **Rejected on inspection.** This conflates "a human clicked one 'Apply' button for an entire extraction run" (Stage 1's actual current UX, per `docs/DOCUMENT-INTELLIGENCE-ARCHITECTURE.md` Section 8) with "a human reviewed and confirmed this specific field" -- Stage 1 has no per-field confirmation UI, only a per-run apply action. Treating a batch-apply click as equivalent to self-reporting each individual fact would be a real, material trust-model weakening, not a resolution -- it reintroduces exactly the risk RB-03 names, just relabeled. This option is documented here because the directive asked for every viable option to be presented, including ones ultimately rejected, but it should not be chosen.

---

## 3. Task 3 -- Recommendation

**Recommended: Option C (generic `DataProvenance` table), implemented for Employment now, with PersonSkill/Competency/Technology migrated onto it in the same change.**

This is a hybrid of B and C: Option B's discipline (solve the actual, present blocker; do not speculatively design provenance for entities with no service layer yet) combined with Option C's structure (so the *next* time this recurs -- and it will, when Education/Certification/Project services are built -- it costs a new enum value, not a new column and a new must-fix-#5-equivalent review).

**Why not plain Option B:** it solves today's problem correctly but guarantees an identical TD-023-shaped problem resurfaces later, at which point the team faces the same "column-per-entity or generic-table" choice again, now with more entities to migrate.

**Why not plain Option A:** it does the speculative six-entity work Option B correctly avoids, for entities with no consuming service yet -- real engineering effort spent on something nobody can exercise until a separate, unauthorized sprint builds those services.

**Why migrate PersonSkill/Competency/Technology onto the new table now, not later:** leaving two provenance mechanisms permanently coexisting (a column on three tables, a generic table for everything else) is a worse long-term state than a one-time, reviewable migration now, while only three tables and one migration guide (`docs/CAREER_DNA_MIGRATION_GUIDE.md`'s established round-trip-verification pattern) are involved.

---

## 4. Task 4 -- Schema evolution design (not implemented, pending approval)

### New table: `data_provenance`
- `id` (UUID PK)
- `subject_type` (enum: `person_skill`, `person_competency`, `person_technology`, `employment` -- extensible by migration, mirroring `EvidenceSubjectType`'s own growth pattern)
- `subject_id` (UUID, polymorphic, NOT a real FK -- same documented trade-off as `EvidenceLink.subject_id`, TD-013)
- `attribution_source` (reuses the `AttributionSource` enum, pending TD-022's resolution on its exact value set)
- `document_extraction_run_id` (nullable FK to `document_extraction_run.id`, `ondelete="SET NULL"` -- traceability to the specific AI extraction, when applicable; null for user-entered/imported data)
- `confidence` (nullable float, populated only when `document_extraction_run_id` is set -- carries `ExtractedField.confidence` through to the applied fact, currently discarded once `apply()` runs)
- `set_at` (timestamp)
- Unique constraint on `(subject_type, subject_id)` -- one provenance record per fact, updated in place (mirroring how `_recompute_attribution` already updates `PersonSkill.attribution_source` in place today, just relocated to a new table).

### Migration plan (two migrations, landed incrementally per this project's established convention)
1. Create `data_provenance` table.
2. Data migration: for every existing `PersonSkill`/`PersonCompetency`/`PersonTechnology` row, insert a corresponding `data_provenance` row from its current `attribution_source` value; then drop the `attribution_source` column from those three tables. **This is a real data migration, not just a schema change** -- requires the same upgrade/downgrade/upgrade round-trip verification this project's `CAREER_DNA_MIGRATION_GUIDE.md` already establishes as the standard, run against real PostgreSQL, not assumed safe from a clean-slate test database.

### Service changes required
- `skill_service.add_person_skill`, `evidence_service._recompute_attribution`, and the (not-yet-built) `employment_service` provenance path all read/write `data_provenance` instead of a column -- one new small internal helper module (`app/services/provenance_service.py`) rather than duplicating the read/write logic in each caller.
- `document_intelligence_service.apply()` gains the ability to write Employment via `employment_service.create_employment` **plus** a `provenance_service.set_provenance(subject_type=EMPLOYMENT, subject_id=..., source=AI_EXTRACTED, document_extraction_run_id=..., confidence=...)` call in the same transaction.
- Every existing PersonSkillRead-style API response that currently reads `.attribution_source` directly on the ORM object instead reads through `provenance_service.get_provenance(...)` -- a real, mechanical but non-trivial refactor across `app/schemas/career_dna.py`'s response construction.

### API changes
- `PersonSkillRead`/future `EmploymentRead`-equivalent gain the same `attribution_source` field in their response shape, now sourced from the join rather than the column -- **no external API contract change**, callers see identical response shapes.

### Tests required (not yet written)
- Data migration round-trip (upgrade populates `data_provenance` correctly from existing columns; downgrade reverses it) verified against real PostgreSQL.
- Every existing Sprint 2 test that currently asserts on `PersonSkill.attribution_source` directly needs updating to go through `provenance_service` -- a real, non-trivial test-suite migration, not just new tests.
- New tests for Employment provenance mirroring the existing Skill attribution tests (`test_attribution_source_not_client_settable`, evidence-linking promotion/demotion equivalents once Employment evidence-linking is designed -- **not yet in scope**, Employment isn't in `_ATTRIBUTION_BEARING_TYPES`/`EvidenceSubjectType` today, and adding it is a further decision this report does not make unilaterally).

---

## 5. Task 5 -- Preserving Sprint 2 guarantees

- **Validation remains enforced:** `provenance_service` is the only writer; `attribution_source` remains absent from every `*Create`/`*Update` Pydantic schema, exactly as must-fix #5 requires -- a client still cannot set `verified` (or now `ai_extracted`) directly through any request body.
- **Ownership remains enforced:** `data_provenance` rows are only ever written/read in the context of an already-ownership-scoped `person`/`document_extraction_run`, via the same `get_current_person` boundary every other Career DNA write already goes through.
- **Provenance remains enforced:** if anything, strictly more so than today -- Employment gains a provenance concept it currently entirely lacks.
- **No direct ORM writes:** `document_intelligence_service.apply()` continues to call service-layer functions only (`employment_service.create_employment`, `provenance_service.set_provenance`), preserving TD-019's write-boundary, now verifiable by extending the existing AST-based boundary test to also check `provenance_service` isn't bypassed.

---

## 6. Task 6 -- New ADR

**Required if Option C is approved.** Drafted as `docs/adr/0007-data-provenance-model.md` -- **not created in this report**, since the directive's Implementation Gate applies to design artifacts that presuppose approval, not just code; it will be written once the recommendation above is accepted, so the ADR reflects a real decision rather than a draft awaiting one.

---

## 7. Independent Architecture Review of this recommendation

Performed as a fresh, adversarial pass against Option C, per the directive's explicit instruction to challenge the recommendation, not confirm it.

**Challenge 1: Is a second polymorphic-reference pattern actually justified, or is this over-engineering relative to Option B?** Genuinely reconsidered. The counter-argument for B is real: YAGNI applies, and TD-013 already flags polymorphic references as an accepted-but-real maintenance cost. **Verdict: Option C survives this challenge** specifically because Employment is very unlikely to be the last entity needing provenance -- Education and Certification are core CV content, and their eventual services will hit this identical question. Paying the polymorphic-pattern cost once, on a pattern the codebase already has one working, tested example of, is cheaper than re-litigating column-vs-table a second or third time.

**Challenge 2: Does migrating PersonSkill/Competency/Technology's existing column onto the new table introduce unnecessary risk to already-shipped, tagged (`v0.2.0-sprint2`) functionality, for a benefit that's purely structural?** This is the strongest objection. Migrating working, tested code carries real risk that pure-Employment-only Option B does not. **Verdict: partially accepts the challenge** -- recommend the migration proceed, but as its own separately-reviewable, separately-testable change within the same approval, not bundled invisibly with the Employment work. If the Chief Architect prefers to defer the PersonSkill/Competency/Technology migration to a later, dedicated pass, Option C's Employment-only slice is still coherent on its own (create `data_provenance`, use it only for Employment, leave the three existing columns alone for now) -- **noting this as a viable reduced-scope variant of the recommendation, not a full rejection of it.**

**Challenge 3: Does `document_extraction_run_id` on every provenance row over-couple Career DNA to the Document Intelligence Engine?** Considered. Rejected as a real problem: the FK is nullable specifically so `USER_ENTERED`/`IMPORTED`/`VERIFIED` rows never reference it, and Career DNA already depends on `document_extraction_run` existing as a concept via `document_intelligence_service.apply()`'s current design -- this makes an implicit dependency explicit and queryable, not a new one.

**Final verdict after adversarial review:** recommendation stands, with the Challenge 2 caveat made explicit as a legitimate reduced-scope fallback if the Chief Architect weighs migration risk more heavily than this report does.

---

## 8. Risk assessment

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Data migration (existing attribution_source columns -> data_provenance) loses or corrupts data | Low, if verified per this project's established round-trip discipline | High (would corrupt Sprint 2's already-shipped data) | Mandatory upgrade/downgrade/upgrade verification against real PostgreSQL before merge, per `CAREER_DNA_MIGRATION_GUIDE.md`'s precedent |
| Test suite migration (updating every test asserting on `.attribution_source` directly) missed somewhere, leaving a silently-broken assertion | Medium | Medium | Full-suite coverage regenerated and diffed against the pre-change 96% baseline; any drop investigated line-by-line, not just re-approved at a lower number |
| Polymorphic reference (TD-013's cost) compounds across two tables now instead of one | Certain (accepted trade-off, not merely a risk) | Low-Medium, ongoing | Same architectural-review-checklist discipline TD-013 already established; no new mitigation invented, existing one extended |

---

## 9. Testing strategy

Mirrors `docs/SPRINT-3-STAGE1-TEST-STRATEGY.md`'s structure: unit tests for `provenance_service` in isolation; a migration round-trip test against real PostgreSQL; integration tests re-verifying every existing Sprint 2 attribution guarantee (dedup, must-fix #5, evidence-linking promotion/demotion) now routed through the new table, not just re-asserting the same behavior against the old column; new Employment-provenance tests mirroring the Skill ones.

---

## 10. Backward compatibility assessment

- **API surface:** no breaking change -- response shapes are unchanged; only the internal source of `attribution_source` moves.
- **Database:** breaking at the schema level (column removed from three tables) but non-breaking at the data level if the migration is verified correctly (every existing value preserved, relocated).
- **`v0.2.0-sprint2` tag:** unaffected -- this is new work building on top of it, not a retroactive change to the tagged commit itself.

---

## 11. Final recommendation, restated plainly

Approve **Option C, Employment-scoped now, PersonSkill/Competency/Technology migration included but flagged as separately reviewable** (Section 7, Challenge 2's caveat). Do not implement until the Chief Architect confirms this scope, including an explicit decision on whether the three-table migration proceeds in the same change or is deferred.
