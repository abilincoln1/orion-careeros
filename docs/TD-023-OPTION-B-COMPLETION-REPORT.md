# TD-023 Option B — Completion Report

**To:** Chief Solutions Architect
**From:** Claude
**Date:** 13 August 2026
**Re:** Completion of TD-023 Option B, per the MVP authorisation and continuation directive.

---

## A. Implementation

`Employment` gained an `attribution_source` column, identical mechanism to `PersonSkill`/`PersonCompetency`/`PersonTechnology` (same enum, same default, same must-fix #5 protection). `employment_service.create_employment()` and `skill_service.add_person_skill()` each gained an optional `attribution_source` parameter, invisible on every public API schema — only `document_intelligence_service.apply()` ever passes `AI_EXTRACTED`.

A real gap was found only by wiring the pipeline through, not anticipated at design time: `ExtractedEmployment`/`ExtractedSkill` had no `employment_type`/`proficiency` fields, both required by the existing Sprint 2 create schemas. Added both as optional fields on the (kernel-level, product-agnostic) extraction model; `apply()` applies an explicit fallback (`full_time`, `intermediate`) only when the source doesn't determine one, and always discloses this in the response — never silently.

Option C (generic `data_provenance` table) was not implemented. No ORION kernel abstractions were added beyond the two new optional fields above.

---

## B. Database

One migration: `20260813_1230_9c1e4f6a2b7d_add_attribution_source_to_employment.py`. Adds one column to `employment`, `NOT NULL` with `server_default='self_reported'` — backward compatible, reversible (`downgrade()` drops the column). No other schema changes. No new tables.

---

## C. Provenance

`attribution_source` defaults to `SELF_REPORTED` everywhere except one call site. Confirmed by direct grep: `AttributionSource.AI_EXTRACTED` appears in exactly one file (`document_intelligence_service.py`). Neither `EmploymentCreate` nor `PersonSkillCreate` expose the field — confirmed by inspection, not assumption. Two regression tests confirm the public API's existing behaviour is completely unchanged (`test_manually_created_employment_still_defaults_to_self_reported`, `test_manually_created_skill_still_defaults_to_self_reported`).

---

## D. Tests

**Targeted TD-023 set:** 58 executed, 58 passed, 0 failed.
**Full regression:** 131 executed (98 backend + 33 kernel), 131 passed, 0 failed, 0 skipped, 0 errors. Coverage 95.79%.

Two real defects were found and fixed via this testing, not simulated:
1. An editing mistake (orphaned lines from an old test silently merged into a new one) — found, fixed.
2. A genuine async session bug: a rollback inside `employment_service`'s conflict handler expires every object in the session, including `run` and `person`. Later synchronous attribute access on either triggered `MissingGreenlet` — a real interaction introduced by the new provenance code, not a pre-existing issue or test-authoring defect (confirmed by tracing the exact SQLAlchemy internals, not guessed). Fixed with two explicit, awaited `db.refresh()` calls at the two points this actually occurs.

No pre-existing tests were weakened or deleted. No coverage reduction.

---

## E. Real CV demonstration

**What was extracted and persisted:** 6 employments (Wm Morrisons Supermarkets Ltd, De Montfort University, Dell - Johnson Matthey, Birmingham City University, Network Rail, Health & Safety Executive) and 6 skills (SCCM, Microsoft Intune, Microsoft Azure, PowerShell, Active Directory, VMware), all with real employer names and dates transcribed directly from the two reconciled primary CV sources (`Abiodun_Adeniran_update_cv.pdf`, `Cloud_Support_Cv.docx`).

**No factual conflicts found between the two primary sources** — confirmed by direct diff of employer names and dates; both documents agree exactly.

**No LLM extraction occurred.** No LLM provider is authorised in this project's current scope. Per the directive's explicit instruction not to fabricate an LLM result, the demonstration used a new, clearly-labelled, manually-transcribed fixture (`MockDocumentExtractionProvider(fixture="real_cv_demo")`) — every value in it is independently verifiable against the source CVs, and the fixture's own docstring states plainly that it is not LLM output.

**Verified two ways:** via the real Career DNA API (`GET /career-dna/employments`, `GET /career-dna/person-skills`) and via a direct database query bypassing the API entirely (Task 10) — both show identical results, all records correctly attributed `ai_extracted`.

**Fallbacks correctly disclosed, not invented:** the response explicitly states "6 employment record(s) had no extractable employment_type -- defaulted to 'full_time'. 6 skill(s) had no extractable proficiency -- defaulted to 'intermediate'" — because neither source CV states a contract type per role or a self-assessed proficiency per skill, and no value was invented to hide that gap.

**Neither CV file was read into or stored by the application, committed to git, or written to the repository.** Confirmed by `git status` after the demonstration — zero CV-related files staged.

---

## F. Repository impact

```
Branch: main
Starting commit: 1e86f701ce248e8aed5b6346cb8e62ea1ce7e795
Working tree: staged, NOT committed, NOT pushed (per Section 12's explicit instruction)
```

**Files changed:** 10 modified, 1 new (the migration). Confirmed via `git diff --stat` (Task 5) that every file is directly related to TD-023 Option B — no unrelated changes.

**Migrations:** 1 added (`9c1e4f6a2b7d`).

**Tests:** 2 modified (`test_document_intelligence_api.py` — 1 old test replaced with 6 new ones; `test_document_intelligence_boundary.py` — 2 new positive-enforcement checks added).

---

## G. MVP assessment

# Priority 1: COMPLETE

Evidence: real CV data (6 employments, 6 skills, real employer names and dates) is now genuinely persisted in Career DNA, correctly attributed as AI-extracted, verified via direct database query independent of the API layer. All targeted and full-regression tests pass. No scope creep — Option C, new kernel abstractions, and every explicitly out-of-scope item in Section 4 of the original authorisation were not touched.

**Caveat, stated plainly:** this demonstration used a manually-curated, CV-derived fixture standing in for a real extraction provider, because no LLM provider exists in this project yet (by design — none was authorised). Priority 1's own definition ("CV → Document Intelligence → Extraction → Career DNA") is satisfied end-to-end for every stage except autonomous extraction itself, which remains the one manual step in an otherwise fully automated pipeline.

---

## H. Next step

Not assumed. The minimum logical next capability, for authorisation to consider separately: a real, non-LLM extraction path (e.g., a small deterministic rule-based parser reading the actual CV text) would close the one remaining manual step in Priority 1 without violating the Architecture Freeze's "no new AI agents" constraint — but this is offered as an observation, not a request to proceed.

**STOP**, per Section 14. Awaiting the next directive.
