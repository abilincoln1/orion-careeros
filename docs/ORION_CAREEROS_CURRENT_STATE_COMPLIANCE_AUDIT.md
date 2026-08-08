# ORION / CareerOS — Current State Compliance Audit

**To:** Chief Solutions Architect
**From:** Claude, acting as independent auditor
**Date:** 2026-08-08
**Repository:** `C:\Projects\Career OS` (`github.com/abilincoln1/orion-careeros`), audited via a fresh clone of `main` at commit `6df3a78`.
**Scope:** CareerOS/ORION only. NDIP (`C:\Projects\NDIP`) was not inspected, referenced, or used as evidence anywhere in this audit -- confirmed by a search of this repository's git history for any NDIP-related filename, which returned no results.
**Method:** Every finding below is either (a) directly observed in this session by reading source files, running the actual test suites, or inspecting git state, or (b) explicitly marked NOT VERIFIED where direct observation wasn't possible in this environment. No claim from a prior compliance report, ADR, or conversation was accepted without checking it against the repository itself.

---

## 1. Executive Summary

CareerOS's Career DNA foundation (Sprint 2) and its API/auth scaffolding (Sprint 1) are real, tested, and match their documentation. Sprint 3 Stage 1 (Document Intelligence Engine) is also real and tested, but its own compliance report's central finding is confirmed here independently: **it cannot yet write AI-extracted employment or skill data into Career DNA with correct provenance.** This is not a documentation gap -- it is a direct, source-level fact, confirmed by reading `skill_service.py` and `employment.py` in this session.

A second finding, not previously stated this precisely in any prior report: **six Career DNA entities (Education, Certification, Project, Achievement, Publication, Reference) have database models but zero service layer and zero API** -- and their test coverage figures are misleading. Coverage tooling reports them at 100%, but this is an artifact of SQLAlchemy model-class definitions executing on import; no test file references any of these six entities at all. "100% covered" and "tested" are not the same claim for this code, and prior reports did not draw that distinction.

**Overall status: AMBER — COMPLIANT WITH CONDITIONS.**
**Stage 2 authorization: NO.**

---

## 2. Repository State

Top-level structure matches what governance documents describe: `platform/` (kernel), `products/careeros/` (backend + frontend), `orion-governance/`, `orion-directives/`, `prompts/`, `docs/`, `scripts/`, `config/`, `data/`, `tests/` (reserved, empty). No unexpected files. No committed `.env` (only `.env.example`, twice -- root and backend). No test/coverage artifacts committed (`.pytest_cache/`, `.coverage` correctly gitignored). `.gitignore` is adequate for what's actually in the repository.

**No NDIP contamination found in git history** -- checked explicitly via `git log --all -- "*D5A*" "*NDIP*"`, zero results.

---

## 3. Git Baseline

| Item | Value |
|---|---|
| Branch | `main` (only branch, no others exist locally or on remote) |
| HEAD | `6df3a78`, committed 2026-08-08 01:17:15 +0100 |
| Remote | `origin` = `github.com/abilincoln1/orion-careeros.git`, fetch and push URLs match |
| Working tree | Clean, no uncommitted changes |
| Local vs. origin | Identical -- `git diff origin/main` returns nothing |
| Tags | One: `v0.2.0-sprint2` |

**Note:** the previous session's earlier confusion involving a stray NDIP file (`D5A_03_06_MIGRATION_MODULES_SEQUENCE_RISK.md`) was resolved by local deletion before it was ever staged or committed -- confirmed above, it does not appear anywhere in this repository's history.

---

## 4. ORION Architecture Assessment

`platform/kernel/orion_kernel/` contains: `config.py`, `database.py`, `health.py`, `logging.py`, `middleware.py`, `security.py`, and `document_intelligence/` (storage, provider, mock_provider, extraction_model, text_extraction). **Checked directly for boundary violations:** `grep -rn "from app\.|import app\." platform/kernel/orion_kernel/` returns zero results. The kernel does not import product code anywhere.

`document_intelligence/` genuinely contains no CareerOS-specific logic -- confirmed by inspection: no import of `app.models`, `app.schemas`, or any Career-DNA-specific name anywhere in that package. The extraction model (`ExtractedPerson`, `ExtractedEmployment`, etc.) is provider- and product-agnostic as designed.

**Verdict: PASS.** Architecture separation is real, not just claimed.

---

## 5. Sprint 1 Compliance

| Requirement | Documented as complete | Demonstrably implemented | Demonstrably tested | Status |
|---|---|---|---|---|
| Platform Kernel (config/logging/security/db/health/middleware) | Yes | Yes -- all 6 modules present | Indirectly, via every backend test that boots the app | PASS |
| User auth (register/login/refresh/me) | Yes | Yes -- `app/api/v1/auth.py`, `app/models/user.py` | Yes -- `test_auth.py`, 6 tests, confirmed passing this session | PASS |
| Health endpoints | Yes | Yes -- `app/api/v1/health.py` | Yes -- `test_health.py`, 4 tests, confirmed passing | PASS |
| Docker containerization | Yes | Yes -- `docker-compose.yml` defines db/backend/frontend with healthchecks | **NOT VERIFIED IN THIS SESSION** -- no Docker available in this audit's sandbox. Real execution evidence exists in prior conversation turns (pasted terminal output showing `docker compose up`, health checks passing, on the project owner's actual Windows/Docker machine, most recently confirmed alongside Sprint 3 Stage 1's PostgreSQL migration run) -- treated as Level 2 evidence from a prior session, not re-verified fresh here. | PASS (on prior session evidence), NOT VERIFIED (this session) |

**Sprint 1: PASS**, with the Docker caveat above stated plainly rather than silently assumed.

---

## 6. Sprint 2 Compliance

Every entity checked against the actual model files, not assumed from documentation:

| Requested entity | Found as | Notes |
|---|---|---|
| Person | `Person` | Present, service + API exist |
| Career Profile | `CareerProfile`, `CareerProfileSnapshot` | Present |
| Employment | `Employer`, `Role`, `Employment` | Present, service + API exist |
| Position/Role | `Role` | Present |
| Project | `Project` | Model only -- **no service, no API** |
| Achievement | `Achievement` | Model only -- **no service, no API** |
| Skill | `Skill`, `PersonSkill` | Present, service + API exist |
| Competency | `Competency`, `PersonCompetency`, `CompetencySkill` | Model only -- **no service, no API** |
| Technology | `Technology`, `PersonTechnology` | Model only -- **no service, no API** (queryable only via `skill_service`'s shared skill-search endpoint, not its own) |
| Programming Language / Platform / Tool | Not separate entities | Consolidated into `Technology` + `TechnologyCategory` enum, per the model's design -- a documented consolidation, not a gap |
| Certification | `Certification` | Model only -- **no service, no API** |
| Education | `Education` | Model only -- **no service, no API** |
| Qualification | Not a separate entity | Not found under this or any other name; not in `CAREER_DNA_MODEL_SPEC.md` either -- appears to have never been part of the approved design, not an implementation gap |
| Publication | `Publication` | Model only -- **no service, no API** |
| Portfolio | `PortfolioItem` | Model only -- **no service, no API** |
| Evidence | `Evidence`, `EvidenceLink` | Present, service exists (`evidence_service.py`), API exists |
| Reference | `Reference` | Model only -- **no service, no API** |
| Career Goal | `CareerGoal` | Model only -- **no service, no API** |
| Work Preference | `WorkPreference` | Model only -- **no service, no API** |
| Salary Preference | `SalaryPreference` | Model only -- **no service, no API** |
| Location Preference | `LocationPreference` | Model only -- **no service, no API** |
| Industry | `Industry` | Present, repository exists (`taxonomy.py`), no direct API |
| Occupation | `Occupation` | Present, same as Industry |
| Job Family | `JobFamily` | Present, same as Industry |

**Finding, stated precisely:** of 24 total Career DNA entities, **4 have a full service + API layer** (Person/CareerProfile, Employment, Skill, Evidence) and **taxonomy lookups exist for 3 more** (Industry, JobFamily, Occupation, via `app/repositories/taxonomy.py`, used internally by skill/employment creation, not exposed as their own endpoints). **The remaining ~14 entities are schema-only** -- migrated into the database, importable, but with no code path that can create, read, update, or delete them.

This matches the TD-023 Resolution Report's own audit finding from the prior session and is independently reconfirmed here by direct file inspection, not merely cited.

**Sprint 2: PASS for the entities actually built and API-exposed (4 of 24), PARTIAL against the full 24-entity model as an inventory of what CareerOS's data model contains.** No document reviewed claims all 24 are API-accessible -- `docs/SPRINT-3-IMPLEMENTATION-PLAN.md` explicitly lists building Education/Certification/Project services as *future* work -- so this is not a contradiction of any existing claim, but it had not been stated this explicitly as a current-state fact before.

---

## 7. Sprint 3 Stage 1 Compliance

| Component | Claimed | Verified this session |
|---|---|---|
| `StorageAdapter` / `LocalStorageAdapter` | Complete | **PASS** -- `platform/kernel/orion_kernel/document_intelligence/storage.py` exists; magic-byte validation, secure path generation, and size limits confirmed by reading the code directly |
| `Document`/`DocumentVersion`/`DocumentExtractionRun` | Complete | **PASS** -- all three classes confirmed present in `app/models/document.py`, with UUID PKs, timestamps, ownership (`person_id`), and lifecycle status fields |
| `DocumentExtractionProvider` + Mock provider | Complete | **PASS** -- both files present; mock provider confirmed to offer 3 deterministic fixtures by reading `mock_provider.py` directly |
| Extraction pipeline (upload -> storage -> provider -> structured extraction -> validation -> Career DNA) | Complete | **PASS** for upload through structured extraction. **PARTIAL** for the Career DNA step -- see Section 9 |
| Intermediate extraction model | Complete, provider-independent | **PASS** -- confirmed no CareerOS-specific import anywhere in `extraction_model.py` |
| Career DNA integration | Partial, by design (TD-023) | **CONFIRMED PARTIAL** -- see Section 9 for the direct source evidence |

**Test evidence, executed fresh in this session:** 91 backend tests passed, 33 kernel tests passed (124 total), 96.26% coverage, both suites run to completion with zero failures. This matches the figures in prior compliance reports -- **no discrepancy found between what was claimed and what actually runs.**

---

## 8. Provenance Assessment

Traced directly through source, not inferred from documentation:

- **Origination:** provenance values are set in exactly two places -- `skill_service.add_person_skill()` (hardcodes `AttributionSource.SELF_REPORTED` at creation, confirmed by reading the function) and `evidence_service._recompute_attribution()` (the only code that can change it afterward, to `VERIFIED` or `INFERRED`).
- **Validation:** no Create/Update Pydantic schema exposes `attribution_source` as a client-settable field -- confirmed by reading `app/schemas/career_dna.py` in full; this is must-fix #5's protection, and it is real, not just documented.
- **Persistence:** `attribution_source` exists as a column on exactly three tables: `PersonSkill`, `PersonCompetency`, `PersonTechnology` -- confirmed via `grep -n attribution_source app/models/*.py`. It does not exist on any other table, including `Employment`.
- **Exposure:** `PersonSkillRead` includes `attribution_source` in its API response shape; no other entity's read schema includes an equivalent field, because no other entity has the underlying column.
- **The four target values** (`USER_ENTERED`/`AI_EXTRACTED`/`IMPORTED`/`VERIFIED`) do **not** match what's actually implemented. The real enum (`app/models/enums.py`) contains five values: `SELF_REPORTED`, `INFERRED`, `VERIFIED`, `AI_EXTRACTED`, `IMPORTED`. `SELF_REPORTED`/`INFERRED` were retained from Sprint 2 rather than renamed/removed, to avoid breaking tested, tagged behavior -- documented as TD-022, open, unresolved.

**Verdict: the system can represent `AI_EXTRACTED` and `IMPORTED` at the schema level (the enum accepts them), but no code path currently writes either value anywhere** -- `document_intelligence_service.apply()` never calls `add_person_skill` or `create_employment` at all (see Section 9), so `AI_EXTRACTED` is a defined-but-dead enum value today, not an exercised one.

---

## 9. TD-023 Assessment (dedicated audit, per Phase 8)

1. **What is TD-023?** A gap preventing the Document Intelligence Engine from writing AI-extracted Employment or Skill data into Career DNA with correct provenance.
2. **Where does it originate?** Discovered during Sprint 3 Stage 1 implementation, when `document_intelligence_service.apply()` was being written.
3. **What code creates the problem?** Two facts, both confirmed by direct source inspection this session: `app/models/employment.py` has no `attribution_source` column at all; `skill_service.add_person_skill()`'s signature (`db, person, payload: PersonSkillCreate`) has no parameter through which a caller could specify provenance.
4. **What provenance constraint causes the problem?** Sprint 2's must-fix #5 (`evidence_service.py`'s design) deliberately keeps `attribution_source` out of every Create/Update schema, so that only evidence-linking can promote a skill's status -- confirmed as a real, enforced constraint (Section 8), not merely documented.
5. **Which Career DNA services are affected?** `skill_service.py` and, structurally, any future `employment_service.py` provenance path (Employment has no provenance concept at all to be "affected" -- it simply lacks one).
6. **Can the current architecture correctly import extracted employment?** **NO.** `employment_service.create_employment()` can be called and will create a row, but nothing on `Employment` records that the data came from an AI extraction -- there is no field to set.
7. **Can it correctly import extracted skills?** **NO**, for the reason in point 3 -- `add_person_skill()` has no provenance input.
8. **Can it correctly preserve provenance?** Only for `Person.headline`, which has no provenance concept to begin with (a plain profile field) -- confirmed by reading `document_intelligence_service.apply()` directly: it calls `person_service.update_person()` for headline only, and explicitly does not call `skill_service` or `employment_service` at all.
9. **Is there an existing workaround?** Yes -- `apply()` writes only `Person.headline`, and returns an `ApplySummary` explicitly stating how many extracted skills/employments were *not* applied, with a note referencing TD-023 by name. Confirmed by reading both the service function and its test (`test_apply_reports_skills_and_employments_not_applied`), which passed in this session's fresh test run.
10. **Would that workaround violate the architecture?** No. It calls only existing service functions, makes no direct ORM writes, and bypasses no validation -- it simply does less than a complete feature would, and says so honestly rather than silently.
11. **Has TD-023 actually been resolved?** **NO.** A resolution report exists (`docs/TD-023-RESOLUTION-REPORT.md`) with a design recommendation (a generic `data_provenance` table, Option C), but zero implementation exists -- confirmed by the absence of any `data_provenance` table in the current migrations (only 4 migrations exist, none post-dating `TD-023-RESOLUTION-REPORT.md`'s commit) and the absence of any `provenance_service.py` file in `app/services/`.
12. **What evidence proves the answer?** `ls alembic/versions/` (4 files, all pre-dating the resolution report), `ls app/services/` (no `provenance_service.py`), and the resolution report's own text explicitly stating "No implementation authorized by this document."

**TD-023 status: Open, unresolved, design-complete, implementation not started, per explicit Implementation Gate.**

---

## 10. Test Assessment

Executed fresh in this session, not cited from a prior report:

| Suite | Result |
|---|---|
| Backend (`products/careeros/backend`) | **91 passed, 0 failed, 0 skipped** |
| Kernel (`platform/kernel`) | **33 passed, 0 failed, 0 skipped** |
| **Total** | **124 passed** |
| Coverage | **96.26%** overall (regenerated via `pytest --cov` this session) |

**Distinguishing "test exists" from "requirement demonstrated":** the six schema-only entities (Section 6) show 100% coverage in the report above, but **zero test files reference `Education`, `Certification`, `Project`, `Achievement`, `Publication`, or `Reference` by name** -- confirmed via `grep -rl` across every test file. Their coverage is an artifact of class-definition execution on import, not behavioral testing. **This means the true, meaningfully-tested surface of the codebase is smaller than the 96.26% headline figure implies for these six entities specifically** -- everywhere else (auth, health, Career DNA's 4 built services, Document Intelligence), the coverage figure does correspond to real behavioral tests, confirmed by reading the test files themselves, not just the coverage tool's summary.

Migration execution: **NOT VERIFIED in this session** (no PostgreSQL available in this sandbox). Prior-session evidence exists (pasted terminal output from the project owner's machine showing all 4 migrations, including the `ALTER TYPE` enum extension, applying cleanly against real PostgreSQL) -- treated as Level 2 evidence from that session, not re-executed fresh here.

---

## 11. Docker Assessment

`docker-compose.yml` defines exactly 3 services: `db` (postgres:16-alpine, with a healthcheck), `backend` (custom image, `depends_on: db`), `frontend` (custom image, `depends_on: backend`). No Redis, no other services -- consistent with CareerOS being a simpler stack than NDIP's (which does use Redis, per this project's own memory of NDIP's architecture, not re-verified here since NDIP is out of scope).

**Runtime readiness: NOT VERIFIED in this session** -- no Docker daemon available in this audit's sandbox. Per the directive's explicit instruction, this is marked NOT VERIFIED rather than inferred from the compose file's static correctness. Prior-session evidence (real `docker compose up`, health checks passing, migrations applying against live Postgres, most recently in the same conversation thread that produced this audit) exists but is not treated as equivalent to fresh verification here.

---

## 12. Documentation Assessment — Truth Table

| Document | Claim | Repository Evidence | Status |
|---|---|---|---|
| `docs/SPRINT-3-STAGE1-COMPLIANCE-REPORT.md` | "91/91 tests passing, 96% coverage" | Confirmed: 91/91, 96.26% | **TRUE** |
| `docs/TD-023-RESOLUTION-REPORT.md` | "No implementation authorized" | Confirmed: no `data_provenance` table, no `provenance_service.py` exists | **TRUE** |
| `docs/SPRINT-2-IMPLEMENTATION-PLAN.md` | Originally scoped 4 entities (Skill/Experience/Project/Technology); superseded by ADR 0004 | Confirmed: superseded, banner present, original text preserved unedited below it | **TRUE, correctly marked historical** |
| `docs/CAREER_DNA_MODEL_SPEC.md` | Describes a ~24-entity model | Confirmed: 24 entities exist as models | **TRUE**, though the spec does not itself distinguish "modeled" from "service-and-API-complete" -- a document-level ambiguity, not a false claim |
| `README.md` | Describes Career DNA and Document Intelligence Engine as implemented | Confirmed true for the entities/features that are; README does not itemize the 4-of-24 API-completeness gap explicitly | **TRUE but incomplete** -- not false, but doesn't surface the gap Section 6 found |
| `docs/metrics.json` | 19 open / 12 resolved technical debt (as of the last regeneration, commit `6df3a78`) | Confirmed matches `docs/TechnicalDebt.md`'s current table counts | **TRUE, current as of this audit's starting commit** |

**No outright false claim was found in any reviewed document.** The gaps found (the 4-of-24 API completeness question, the misleading 100%-coverage-on-untested-entities artifact) are omissions -- things not yet stated anywhere -- rather than contradictions of anything actually claimed.

---

## 13. Governance Assessment

Traceable chain checked for the two most recent significant decisions:

**Career DNA acceptance (Sprint 2):** Architecture Decision (`CAREER_DNA_MODEL_SPEC.md`) -> Chief Architect directive (Sprint 1.6 Candidate Acceptance Review) -> Implementation (already existing, reviewed retroactively) -> Tests (91 backend tests exist and pass) -> Compliance Report (Sprint 1.6's own) -> Acceptance (Chief Architect's "Approve" recommendation) -> Git Tag (`v0.2.0-sprint2`). **Chain complete.**

**Document Intelligence Engine (Sprint 3 Stage 1):** Architecture Decision (ADR 0006) -> Chief Architect directive (Stage 1 Implementation Authorisation) -> Implementation (commit `51167f2`) -> Tests (124 passing, confirmed) -> Compliance Report (`SPRINT-3-STAGE1-COMPLIANCE-REPORT.md`) -> Acceptance -> **Git Tag: MISSING.** No tag exists for Stage 1. This is consistent with the Chief Architect's own directive ("Stage 1 is NOT closed... Approved with Conditions") -- the missing tag is not an oversight, it is the correct reflection of Stage 1's actual, still-open status.

**Missing link found:** `orion-directives/` contains only a `README.md` (explaining the intended structure and flagging that historical directives were never backfilled) -- no actual directive files exist in that directory yet. The directives that *have* been saved as files live in `prompts/` (`Chief_Architect_Directive_Sprint03.md`, `Chief_Architect_Directive_Sprint3_Stage1_Completion.md`), per each directive's own explicit save-location instruction at the time. This is a known, previously-flagged gap (in the `orion-directives/README.md` itself), not a new finding.

---

## 14. Technical Debt (current register state)

19 open, 12 resolved, per `docs/TechnicalDebt.md` as of commit `6df3a78` -- confirmed by direct count (`grep -c`) in this session, matching `docs/metrics.json`. Highest-severity open items: **TD-023 (Critical)**, **TD-013 (High)**, **TD-024 (Medium-High, dependency vulnerabilities, filed in the prior full-project audit)**.

---

## 15. Risks

`docs/RiskRegister.md` currently tracks RB-03 (AI-extracted data trust/provenance risk) as **Open** -- correctly reflecting TD-023's unresolved state; the register has not prematurely marked this risk closed while the underlying gap remains. No other open risk items were found to contradict current repository state upon inspection.

---

## 16. Contradictions Found

**None** between documentation and repository evidence, at the level of explicit claims actually made. The findings in this audit (Section 6's 4-of-24 API completeness, Section 10's coverage-artifact distinction) are **new information surfaced by deeper inspection**, not corrections of prior false statements.

---

## 17. Evidence Gaps

- **Docker runtime verification** (this session) -- no Docker available in this sandbox; relying on prior-session, human-operator-executed evidence rather than re-verification here.
- **PostgreSQL migration execution** (this session) -- same limitation, same reliance on prior-session evidence.
- **Frontend** -- not audited in any depth in this report; the directive's phases focus on backend/data/governance, and the frontend received no dedicated inspection here.

---

## 18. Current Project Status

# AMBER — COMPLIANT WITH CONDITIONS

Sprint 1 and the built portions of Sprint 2 are genuinely compliant. Sprint 3 Stage 1's infrastructure is genuinely compliant. The conditions blocking a GREEN status are specific and named, not vague: TD-023 (Critical, unresolved), TD-024 (Medium-High, unresolved), and the newly-surfaced 4-of-24 Career DNA API completeness gap (not itself a defect, but a scope fact that should be stated plainly going forward rather than left implicit).

---

## 19. Recommended Next Gate

Resolve TD-023's scope decision (Employment-only vs. including the PersonSkill/Competency/Technology migration, per the resolution report's Option C) **before** any Stage 2 work begins. TD-024 (dependency vulnerabilities) should be evaluated in parallel, not sequentially -- it does not depend on or block the TD-023 decision. Once both are resolved and implemented, tested, and tagged, Stage 1 can be formally closed with a git tag, and Stage 2 can be authorized on a clean, fully-closed foundation rather than an open one.

---

# CRITICAL DECISION

> **Is CareerOS currently authorised to proceed to Sprint 3 Stage 2?**

## NO

**Evidence supporting this decision:** TD-023 remains open and unimplemented (Section 9, confirmed by direct source inspection, not by citation of a prior report). The Chief Architect's own prior directive already states Stage 2 remains frozen until TD-023 is resolved, Stage 1 is formally accepted, Stage 1 is tagged, and the Engineering Release Package is complete -- none of those four conditions are met as of this audit (no `data_provenance` implementation exists, no Stage 1 tag exists, no closing Engineering Release Package has been assembled). This audit independently confirms the prior directive's blocking conditions are still actually true in the repository, not merely still true on paper.
