# Project ORION -- Full Engineering Audit Report

**To:** Chief Solutions Architect (ChatGPT), ORION Architecture Review Board
**From:** Claude (Anthropic), engineering assistant
**Date:** 2026-08-06
**Scope:** Entire project history, commit `fc38096` through `e6bf867`, repository `abilincoln1/orion-careeros`.
**Basis:** Every figure below is drawn from a fresh clone and, where a metric is stated, from re-running this project's own tooling (`scripts/metrics/collect_metrics.py`, `pytest --cov`) at the time this report was written -- not from memory of earlier sessions. Where something could not be independently re-verified in this environment, that is stated explicitly.

---

## 1. Executive summary

Project ORION has progressed through eleven commits and six architecturally significant phases since Sprint 1's baseline: Sprint 1 Closure, a governance crisis (Sprint 1.5) and its remediation (Sprint 1.6), Sprint 2's formal acceptance (`v0.2.0-sprint2`), a governance-framework sprint (Sprint 3 Phase 0-6), and Sprint 3 Stage 1 (Document Intelligence Engine), which is currently **paused at an architectural gate (TD-023)** pending Chief Architect decision.

**Current state:** 124 tests passing (91 backend, 33 platform kernel), 96.26% code coverage, 4 database migrations, 31 API endpoints, zero kernel/product boundary violations. **19 open technical debt items (18 plus TD-024, filed by this audit), 12 resolved.** One new, previously-unreported finding surfaced while compiling this audit: **59 known dependency vulnerabilities**, up sharply from the 22 last formally reported, driven mainly by `pypdf` (37 of the 59) -- see Section 6, now filed as TD-024.

**The project's defining characteristic across this history is not the absence of mistakes, but a consistent pattern of finding real defects through actual verification (not assumption) and correcting them transparently** -- documented drift, dialect-specific bugs, a coverage-measurement gap, and now a provenance-architecture gap have each been found, reported honestly, and either fixed or explicitly gated pending decision, rather than glossed over.

---

## 2. Timeline and what each phase actually delivered

### Sprint 1 / Sprint 1 Closure (commit `fc38096`, `8c59101`)
Platform Kernel foundation (config, logging, security, database, health, middleware) and CareerOS's initial auth/user scaffolding. Baseline established.

### Sprint 1.5 -- Repository Reconciliation
**Trigger:** a routine compliance check found the Career DNA schema (24 entities, already implemented) directly contradicted README.md, `SPRINT-1-ACCEPTANCE-REPORT.md`, and `RiskRegister.md`, all of which stated in the same commit that it did not exist and was unauthorized. Root cause determined to be documentation/governance failing to track completed, deliberate, spec-driven work -- not unauthorized or defective engineering.
**Outcome:** A five-phase reconciliation (inventory, drift classification, disposition recommendation) recommending "review, then accept" over rewrite or removal.

### Sprint 1.6 -- Candidate Acceptance Review (commit `5484f1f`)
Independent, adversarial review of the Career DNA implementation. **Found and fixed 4 real defects**, none anticipated:
- A validation-handler crash affecting every custom Pydantic validator in the codebase (`app/main.py`).
- A cross-dialect bug where a conflict-detection check worked against PostgreSQL but silently failed under SQLite (`employment_service.py`).
- A test-infrastructure gap: SQLite wasn't enforcing foreign keys, meaning every `ON DELETE CASCADE` relationship in the schema had been silently untested.
- A coverage-measurement gap: no `.coveragerc` existed, so `coverage.py` was undercounting async service-layer code project-wide -- correcting it took measured coverage from 83% to 96% with the *same* test suite, no new tests required to reveal it.

Test coverage went from 0% on Career DNA to 96.01%, verified identically against both SQLite and real PostgreSQL. **Tagged `v0.2.0-sprint2`.**

### Sprint 3 Phase 0-6 -- Governance Framework + Job Intelligence Architecture (commit `f751d6e`, `8e311b7`)
Built `/orion-governance` (10 migrated + 10 new standards/templates/checklists documents, each grounded in a real defect this project had actually found, not generic boilerplate). Designed the Job Intelligence Platform architecture (5 components: CV Intelligence, Job Intelligence, Matching Engine, Recruiter Watchlist, Interview Pipeline) -- design only, no implementation, per explicit directive.

An independent Phase 6 review of that design (self-review by the same author who wrote it, flagged as a real limitation, not claimed as fully independent) found **5 Must-fix defects**, including one that would have reintroduced a pattern class already fixed once (a JSON-blob status history contradicting the project's own established "history as rows, not blobs" principle from ADR 0004). **Recommendation: Approve with Conditions.**

Five foundational decisions resolved by the Chief Architect (ADR 0005): File Storage stays CareerOS-local; Scheduling becomes a genuine Platform capability; a new AI-attribution provenance model introduced; `JobListing` uses soft-deletion; a proposed `/shared` repository restructure deferred (TD-018, closed).

### Sprint 3 Stage 1 -- Document Intelligence Engine (commits `1713e6c`, `51167f2`)
Redirected mid-design from a CareerOS-local "CV Intelligence" parser to a genuine, reusable Platform Kernel capability (ADR 0006), on the explicit reasoning that cross-product reuse -- unlike File Storage's case -- was this capability's stated purpose, not a speculative future benefit.

Design phase found and fixed 5 more Must-fix defects before any code was written (undefined types, an unresolved RSS/API pagination ambiguity, an unspecified secrets mechanism, a missing storage interface, and -- again -- a JSON-blob-for-history pattern, this time in `Application.status_history_json`).

Implementation delivered: storage layer, `Document`/`DocumentVersion`/`DocumentExtractionRun` domain model (with versioning built in from the start per a Chief Architect suggestion, not deferred), 2 migrations, a provider abstraction with a complete mock testing surface, real PDF/DOCX text extraction, and a full API surface. **91 backend + 33 kernel tests, 96% coverage, verified on real PostgreSQL.** Two more real defects found and fixed during testing (a `python-docx` exception-handling gap, a missing eager-load).

**Critical finding, not worked around:** neither `Employment` nor `PersonSkill` can currently be written with correct AI provenance through the existing, unmodified Sprint 2 services -- `Employment` has no provenance field at all, and `skill_service.add_person_skill()` deliberately has no provenance parameter, by design, per Sprint 2's own must-fix #5. Rather than bypass validation or mislabel AI-extracted data as user-entered (both explicitly forbidden), the implementation applies only `Person.headline` and honestly reports what wasn't applied and why. **Filed as TD-023, Critical.**

### TD-023 Resolution Report (commit `e9a0c30`) -- current position
A full provenance-pipeline audit (every Career DNA entity checked for where provenance is written/consumed) found the underlying design question was more precise than originally framed: Sprint 2 had *deliberately* scoped provenance to exactly 3 entities, and most of the entities TD-023 worried about have no service layer at all yet. Four options were designed and compared (full symmetry, Employment-only, a generic polymorphic `data_provenance` table, and a rejected "no schema change" option). **Recommendation: a generic `data_provenance` table, scoped to Employment now**, with the existing 3-column migration flagged as separately reviewable after an adversarial self-review found real migration risk in bundling it. **No implementation has occurred. Stage 2 remains frozen**, per the Chief Architect's explicit directive, pending this decision.

---

## 3. Current verified state

| Metric | Value | Verification |
|---|---|---|
| Test count | 124 (91 backend + 33 kernel) | Collected fresh this session |
| Code coverage | 96.26% | Regenerated this session via `scripts/metrics/collect_metrics.py` |
| Migrations | 4 | `alembic history`, single head, no branches |
| API endpoints | 31 (regex count; more by hand, including kernel-provided health routes) | Regenerated this session |
| Architecture compliance | Compliant -- 0 instances of kernel importing product code | Regenerated this session |
| Technical debt | **18 open, 12 resolved** | Regenerated this session |
| Lines of code | 3,517 (CareerOS backend), 1,009 (kernel), 1,494 (tests) | Regenerated this session |
| Git tags | `v0.2.0-sprint2` | `git tag` |
| ADRs | 6 (0001-0006), all indexed | `orion-governance/architecture/ADR_INDEX.md` |

---

## 4. Open technical debt, by severity

**Critical (1):**
- **TD-023** -- Career DNA provenance gap. Resolution designed, awaiting Chief Architect scope decision. Blocks Stage 2.

**High (1):**
- **TD-013** -- `EvidenceLink.subject_id` polymorphic-reference cleanup relies on service-layer discipline with no DB-level backstop. (Note: the TD-023 recommendation would introduce a second instance of this same pattern -- worth weighing together, not independently.)

**Medium (5):**
- **TD-012** -- Platform Kernel cross-repository distribution gap (dormant until a second ORION product exists).
- **TD-014 through TD-016** -- resolved, listed here only if reader is cross-checking; actually in the Resolved table, not Open (see Section 5 correction note).
- **TD-022** -- `AttributionSource` naming reconciliation between Sprint 2's original 3-value set and the Chief Architect's approved 4-value provenance model.
- **TD-019/020/021** -- Stage-specific Definition-of-Done gates (write-boundary enforcement -- now satisfied; provider test fixtures for a *future* Job Intelligence provider, not Stage 1's own mock; `MatchResult` Person-cascade, pending Stage 3).

**Low (11):** dead code (`app/repositories/base.py`, TD-017), the deferred `/shared` restructure (closed as TD-R12), and other minor, non-blocking items -- full detail in `docs/TechnicalDebt.md`.

---

## 5. Governance record integrity check

Per `orion-governance/engineering/ConfigurationIntegrityStandard.md`, applied to the whole project as of this audit:

| Artefact | Consistent with code? |
|---|---|
| Specifications (`CAREER_DNA_MODEL_SPEC.md`, `DOCUMENT-INTELLIGENCE-ARCHITECTURE.md`) | Yes |
| ADRs (0001-0006) | Yes, all reflect actual implemented or explicitly-deferred decisions |
| Source code | Ground truth; matches all reports above, re-verified this session |
| Tests | 96.26%, re-measured this session, not assumed from a prior report |
| Documentation | README, ARCHITECTURE.md current as of Sprint 3; two historical reports (`SPRINT-1-ACCEPTANCE-REPORT.md`, `SPRINT-2-IMPLEMENTATION-PLAN.md`) carry supersession banners rather than edits, per project convention |
| Governance (`RiskRegister.md`, `TechnicalDebt.md`) | Current; RB-01's false "Mitigated" claim corrected in Sprint 1.6; RB-03 tracks the live provenance-trust risk TD-023 addresses |
| Metrics | **Was stale prior to this audit** (last regenerated before Stage 1 landed) -- regenerated as part of compiling this report; now current |

**One inconsistency found and corrected in the course of writing this audit:** `docs/metrics.json` had not been regenerated since before Stage 1's implementation landed, meaning the last committed figures (13 open/11 resolved debt, 96.01% coverage, 25 endpoints) were stale relative to the actual repository state (18 open/12 resolved, 96.26%, 31 endpoints). Regenerated and included in the figures above; recommend committing the refreshed `docs/metrics.json` in the next commit rather than leaving this audit as the only current record of it.

---

## 6. New finding, surfaced by this audit: dependency vulnerabilities

Not previously reported at this level of detail. Running this project's own security scan during metrics regeneration found **59 known vulnerabilities**, concentrated in:

| Package | Version | Known vulnerabilities |
|---|---|---|
| `pypdf` | 5.1.0 | 37 |
| `starlette` | 0.41.3 | 9 |
| `python-multipart` | 0.0.20 | 6 |
| `python-jose` | 3.3.0 | 5 |
| `pytest` | 8.3.4 | 1 |
| `ecdsa` | 0.19.2 | 1 |

This is a substantial jump from the 22 vulnerabilities tracked under TD-011 prior to Stage 1 -- `pypdf` alone (introduced by Document Intelligence's text extraction, Stage 1) accounts for more new findings than the entire prior baseline. **This was not flagged in the Stage 1 Compliance Report** and should have been -- recorded here as a gap in that report's own thoroughness, not attributed to any hidden cause. **Filed as TD-024** in this audit; recommend evaluating whether a `pypdf` version bump resolves the bulk of it, separate from and not blocking the TD-023 decision.

---

## 7. Process observations, across the full history

- **The project's self-correction pattern is real and repeated, not a one-off.** Sprint 1.5's reconciliation, Sprint 1.6's four defects, the Phase 6 review's five Must-fixes, Stage 1's own five design-phase Must-fixes plus two implementation-phase bugs, and TD-023 itself all follow the same shape: find something real through actual verification, report it plainly, fix or explicitly gate it. This is evidence the review discipline this project has built is functioning, not evidence of an unusually error-prone process.
- **Every "independent" architecture review to date has been a fresh reading pass by the same AI that authored the design, not a genuinely separate reviewer.** This has been disclosed each time it occurred (Sprint 1.6, Phase 6, Stage 1's own review), but is worth naming once, plainly, in a full audit: it is a real, structural limitation on how independent these reviews actually are, regardless of how adversarially they were conducted.
- **Verification against real PostgreSQL has consistently lagged behind SQLite-based sandbox verification**, requiring the project owner's own machine each time -- this has worked, but represents a recurring manual step this project has not yet automated (see TD-006, CI, still open and unaddressed since Sprint 1).

---

## 8. Recommendation

No new disposition is requested by this report -- it is a status audit, not a decision point. For the Chief Architect's awareness heading into the next decision:

1. **TD-023's scope decision remains the single blocking item** for Stage 1 closure and Stage 2's start, exactly as the prior directive established.
2. **TD-024 (dependency vulnerabilities, filed by this audit) should be evaluated in parallel**, not as a blocker to the TD-023 decision, but as its own tracked item before Stage 1 is formally tagged and closed -- a formal Stage 1 closure that doesn't account for a tripled vulnerability count would itself be a Configuration Integrity gap of the kind this project has otherwise been careful to avoid.
3. **`docs/metrics.json` should be committed in its refreshed state** in whatever commit closes out this audit, so the repository's own metrics file doesn't remain the stale artifact this audit found it to be.
