# Project ORION -- Compliance Report

**To:** Chief Solutions Architect
**From:** Claude (Anthropic), engineering assistant
**Date:** 2026-08-06
**Re:** Sprint 3 Stage 1 (Document Intelligence Engine) -- implementation compliance assessment, commit `51167f2`.

---

## 1. Purpose

This report assesses Stage 1 (Document Intelligence Engine) against the Sprint 3 v1.1 directive's Stage 1 scope, the Phase 6 Architecture Review's three Approve-with-Conditions items, and this project's own engineering standards (`orion-governance/engineering/DefinitionOfDone.md`, `QualityGates.md`). Every claim below is backed by a command actually run and its output actually read -- either in this session or by the project owner on the target Windows/Docker/PostgreSQL environment, with results pasted back and verified. Where something could not be verified, that is stated plainly.

**Headline finding:** Stage 1's infrastructure (storage, domain model, migrations, provider abstraction, extraction pipeline, API surface) is complete, tested, and verified on real PostgreSQL. Its Career DNA integration is **deliberately incomplete** -- a real architectural gap was found during implementation, not worked around, and is documented below as the primary open item.

---

## 2. What was found / done

### 2.1 Directive scope -- Phases 1-7

| Phase | Deliverable | Status |
|---|---|---|
| 1 | `StorageAdapter` interface, `LocalStorageAdapter`, file/MIME/size validation, secure path generation, unit tests | **Complete.** 9 unit tests, real path-traversal and mismatched-content-type cases covered. |
| 2 | `Document`, `DocumentVersion`, `DocumentExtractionRun` -- UUID, timestamps, ownership, provenance, lifecycle state, audit metadata | **Complete.** Versioning (Document -> DocumentVersion -> DocumentExtractionRun) implemented from the start, per the Chief Architect's roadmap suggestion, not deferred. |
| 3 | Reversible migration, PostgreSQL-verified, SQLite-compatible, indexed, FK integrity, cascade behavior verified | **Complete and verified on real PostgreSQL** (via `bootstrap.ps1`, confirmed by the project owner -- migrations, including the `ALTER TYPE ... ADD VALUE` on `attribution_source`, applied cleanly). |
| 4 | `DocumentExtractionProvider` interface, `MockDocumentExtractionProvider` as the complete testing surface, no production LLM | **Complete.** Three deterministic fixtures (clean/low-confidence/partial) plus a simulated health-check failure. No LLM API called anywhere in this codebase. |
| 5 | Extraction pipeline: upload -> storage -> provider -> structured extraction -> validation -> Career DNA services | **Complete for the upload-through-validation stages.** Career DNA integration stage is intentionally partial -- see Section 3. |
| 6 | Canonical extraction objects (`ExtractedPerson`, `ExtractedEmployment`, etc.), provider-independent | **Complete.** Deliberately has zero import dependency on any CareerOS-specific schema, confirmed by inspection -- this is what makes the objects genuinely reusable by a future ORION product, not just documented as such. |
| 7 | Career DNA integration -- existing services only, no duplicate business logic, no bypassing validation, no direct ORM writes | **Partially complete, by design.** See Section 3 -- this is not a shortcut; it is the correct response to a real constraint found during implementation. |

### 2.2 AI Provider Policy compliance

No OpenAI, Anthropic, Azure, Google, Amazon, Affinda, or Sovren integration exists anywhere in this codebase. `get_extraction_provider()` (the sole place a provider is selected) returns `MockDocumentExtractionProvider` unconditionally. Confirmed by inspection, not merely by absence of a bug report.

### 2.3 Test completion, verified on both SQLite and PostgreSQL

- **91/91 tests passing**, **96% coverage**, identical results on this session's SQLite sandbox and the project owner's real PostgreSQL container (pasted output, both runs).
- Kernel-level tests (33) run independently of the CareerOS backend, confirming the Document Intelligence Engine's provider-agnosticism is enforced by the test suite's own structure, not just claimed in comments.
- TD-019's write-boundary condition (Phase 6 review) has an actual enforcement mechanism: a static AST-based test (`test_document_intelligence_boundary.py`) that fails the build if `document_intelligence_service.py` ever imports a forbidden Career DNA model directly.

### 2.4 Real defects found and fixed during implementation

Per this project's Truth First principle, these are reported because finding and fixing them is evidence the process works, not omitted to make the report look cleaner:

1. `python-docx` raises `zipfile.BadZipFile` (not `PackageNotFoundError`) for a malformed DOCX -- caught by a real corrupt-file test, fixed by catching both exception types.
2. `Document.versions` failed to serialize (`MissingGreenlet` error) because the relationship wasn't eagerly loaded -- caught by a real API test, fixed with `lazy="selectin"`, matching the existing `Employment.employer` pattern.

Neither defect was anticipated; both were found by tests actually exercising the code, not by static review.

---

## 3. The primary open item: TD-023 (Critical)

**Finding:** Neither `Employment` nor `PersonSkill` can currently be written with correct AI provenance through the existing, unmodified Sprint 2 services.

- `Employment` has no `attribution_source` column at all.
- `skill_service.add_person_skill()` does not accept `attribution_source` as a parameter -- **by design**, per Sprint 2's own must-fix #5, specifically to prevent a client from claiming `verified` directly.

Writing extracted skills or employment history through those functions unmodified would silently mislabel AI-extracted data as user-entered data. This is precisely the trust-model violation RB-03 exists to name.

**What was NOT done, and why:** bypassing validation, writing directly to the ORM, or silently reusing `self_reported`/leaving attribution unset were all considered and rejected -- each would either violate the directive's explicit "no bypassing validation, no direct ORM writes" instruction or produce exactly the mislabeling RB-03 warns against.

**What was done instead:** `apply()` writes only `Person.headline`, and only when currently unset (never overwriting a user-entered value). Every response explicitly states what was NOT applied and why (verified by a passing test asserting the response text references TD-023/attribution, not a silent zero).

**Practical consequence:** Stage 1, as it stands, can extract structured data from a CV but can only apply the person's headline to their Career DNA profile. It cannot yet populate employment history or skills -- the two things a CV-focused tool exists to extract. This is a real, material scope gap, not a footnote.

**Resolution requires a decision, not more engineering:** either (a) extend `Employment`/`Education`/`Certification`/`Project`/`Achievement` with `attribution_source`, and/or (b) add an optional, still-validated `attribution_source` override to `add_person_skill()`/`create_employment()` -- both are reviewable Sprint 2 schema/service changes that should go through the same rigor Sprint 2's original must-fixes did, not be decided unilaterally during Stage 1.

---

## 4. Secondary open item: TD-022

`AttributionSource`'s approved provenance set (`USER_ENTERED`/`AI_EXTRACTED`/`IMPORTED`/`VERIFIED`) does not include `INFERRED`, which Sprint 2's tested evidence-demotion logic depends on. Resolved for now by additive extension (5 values total, nothing renamed or removed) rather than silently breaking accepted, tagged behavior. Needs a reconciliation decision: accept the 5-value enum as final, or authorize a reviewed migration consolidating it to the approved 4.

---

## 5. Governance record updates this session

- **TD-022, TD-023 added** (`docs/TechnicalDebt.md`), both flagged for Chief Architect decision rather than resolved unilaterally.
- **No RiskRegister changes this session** -- RB-03 (added at Phase 6) already covers the provenance-trust risk TD-023 materializes; no new risk category is needed, only closure of the existing one once TD-023 is resolved.
- **No new ADR this session.** The implementation followed ADR 0005/0006 as designed; the TD-023 finding is a service-layer gap discovered during implementation, not a new architectural decision -- an ADR is appropriate once its resolution (schema extension vs. service-signature change) is chosen, not before.

---

## 6. Recommendation

**Stage 1 infrastructure: Approve.** Storage, domain model, migrations, provider abstraction, and extraction pipeline meet every stated requirement, verified on real PostgreSQL, with 96% coverage and both Phase 6 review conditions (write-boundary enforcement, provider test fixtures) satisfied by actual mechanisms, not policy statements.

**Stage 1 Career DNA integration: Approve with Conditions -- do not consider Stage 1 feature-complete until TD-023 is resolved.** The partial scope was the correct call given the constraint found, but it should not be silently accepted as "done." Recommend treating TD-023's resolution as a prerequisite gate before Stage 2 (Job Provider Framework) begins, since Stage 2 will surface the identical question for `JobListingSkill`/`JobListingTechnology` extraction -- resolving it once now is cheaper than re-deriving the same decision mid-Stage-2.

**Not recommended:** proceeding to Stage 2 while treating Stage 1 as fully closed. The infrastructure is genuinely done; the feature it exists to enable is not yet, and that distinction matters for anyone reading Stage 1's status later without this report's context.

---

## 7. Outstanding items, carried forward explicitly

- TD-023 (Critical) -- Career DNA write-path attribution gap, blocking Skills/Employment application.
- TD-022 (Medium) -- `AttributionSource` set reconciliation.
- TD-019 condition -- satisfied (enforcement mechanism in place); no longer open.
- TD-020 condition (Stage 2 provider fixtures) -- satisfied for Stage 1's own `MockDocumentExtractionProvider`; Stage 2's Job Intelligence provider fixtures remain a separate, not-yet-started item.
- TD-021 condition (`MatchResult`/`Person` cascade) -- unaffected by this stage, still pending Stage 3.
