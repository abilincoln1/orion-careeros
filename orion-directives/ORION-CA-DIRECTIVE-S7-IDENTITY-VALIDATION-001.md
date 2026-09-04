# Project ORION / CareerOS — Chief Architect Directive

**Directive ID:** `ORION-CA-DIRECTIVE-S7-IDENTITY-VALIDATION-001`
**To:** Claude, Engineering Assistant
**From:** Chief Solutions Architect / ORION Architecture Review Board
**Date:** 19 August 2026
**Subject:** Applications Packager Identity Validation — Analysis and Controlled Execution

---

## 1. Authority and Purpose

You are authorised to perform **one narrowly scoped validation experiment** following the findings of:

* `ORION-CA-DIRECTIVE-S4-RELEVANCE-001`
* `ORION-CA-DIRECTIVE-S5-DISCOVERY-QUERY-ENRICHMENT-001`
* `ORION-CA-DIRECTIVE-S6-DISCOVERY-RETRIEVAL-DIAGNOSTIC-001`

The published repository state remains:

```text
v0.5.0-ui-mvp
HEAD: 56bccb2
```

No existing release tag may be moved, rewritten, deleted, or otherwise altered.

The purpose of this directive is to test one specific hypothesis identified by the S6 diagnostic:

> The candidate's repeatedly evidenced **Applications Packager** career identity may represent the candidate more accurately for Job Discovery than the current single-most-recent-role heuristic.

This directive does **not** authorise a new discovery architecture.

---

# 2. Critical Repository Gate — Execute Before Any Experiment

The repository must first be inspected because the current working tree is not assumed to be clean.

Run:

```powershell
git status
git status --short
git diff --cached --stat
git diff --cached
```

The expected known state from the latest compliance report is:

### Staged documentation

```text
docs/DISCOVERY-RELEVANCE-VALIDATION-REPORT.md
docs/S5-DISCOVERY-QUERY-ENRICHMENT-IMPLEMENTATION-REPORT.md
docs/S5-FINAL-VALIDATION-REPORT.md
docs/CAREEROS-DISCOVERY-RETRIEVAL-DIAGNOSTIC.md
orion-directives/ORION-CA-DIRECTIVE-S4-RELEVANCE-001.md
orion-directives/ORION-CA-DIRECTIVE-S5-DISCOVERY-QUERY-ENRICHMENT-001.md
orion-directives/ORION-CA-DIRECTIVE-S6-DISCOVERY-RETRIEVAL-DIAGNOSTIC-001.md
```

### Deliberately untracked

```text
docs/CAREEROS-INTERVIEW-ACQUISITION-MVP-VALIDATION.md
docs/JOB-DISCOVERY-POST-RELEASE-ASSESSMENT.md
```

Do not assume this state is correct. Verify it.

## Repository handling rule

Do **not** accidentally include any of the existing staged or untracked files in an experiment commit.

Do not run `git add -A`. Do not run `git commit -am`.

No commit is authorised under this directive unless explicitly authorised after review of the final validation report.

---

# 3. Hypothesis Under Test

> Using **Applications Packager** as the discovery query produces a materially more useful balance of relevance and result volume than the current discovery representation.

The S6 diagnostic found that: "Applications Packager" appears in multiple real employment records; it represents the strongest repeated employment identity in the candidate's actual Career DNA; it is supported by a cluster of directly relevant skills; the current production heuristic does not necessarily select it because it uses only the latest employment title.

---

# 4. Exact Scope

The primary experiment query is:

```text
Applications Packager
```

You may inspect the exact current discovery and matching pipeline before execution. You may make the **smallest temporary change necessary** to cause this exact query to travel through the existing discovery pipeline. The objective is to test the identity, not to redesign query construction.

The existing `Provider → live Arbeitnow inventory → existing local filtering → existing persistence → existing UI/API surface` should remain materially unchanged.

---

# 5. Explicitly Forbidden

Multi-query discovery; combining "Applications Packager" with the latest employment title; combining multiple career identities; skill enrichment; skill-overlap matching; ranking or scoring; weighting algorithms; new database tables; schema changes; new Career DNA entities; changes to Document Intelligence; changes to Career DNA persistence; a second job provider; JobServe/Totaljobs/Indeed integration; application tracking; interview pipeline functionality; autonomous job applications; LLM-based query generation; generalised multi-identity architecture.

Do not "improve" the experiment while performing it.

---

# 6. Baseline

```text
Broad-query baseline: ~30 listings reviewed
Highly Relevant: 0, Relevant: 1, Possibly Relevant: 5, Irrelevant: 24
Highly Relevant + Relevant: 1/30 ≈ 3.3%

S5 enriched experiment:
Highly Relevant: 1, Relevant: 2, Possibly Relevant: 1, Irrelevant: 0
Highly Relevant + Relevant: 3/4 = 75%
Total available results: 4
```

That experiment was correctly classified as a regression because the result volume collapsed to near zero. Do not combine the S5 experiment with this experiment; this is a separate test.

---

# 7. Required Execution

Step 1: Confirm baseline (`git status`, `git rev-parse HEAD`, `git describe --tags --exact-match HEAD`; run the backend regression suite; record test count/passed/failed/database environment; do not proceed if baseline is already failing).

Step 2: Inspect the current pipeline — where the query is derived, where it enters the provider/filtering process, where matching occurs, whether "Applications Packager" requires a temporary code change or can be injected through an existing API mechanism. Prefer an existing request override if one genuinely exists; do not invent one merely for convenience.

Step 3: Run the exact experiment using the real candidate, real PostgreSQL, live Arbeitnow API, existing provider, existing matching/filtering logic. Do not use mocked provider data as primary evidence. Record query used, time/date, provider response size, listings found/new/duplicate, total matching result set. Inspect the actual returned listings.

---

# 8. Manual Relevance Review

Review up to the first 30 distinct returned listings (or the entire result set if fewer than 30). Classify using the established categories: Highly Relevant / Relevant / Possibly Relevant / Irrelevant. Do not change definitions after seeing results. Record job title, company, location, classification, short justification for each. Do not inflate classifications to make the experiment appear successful.

---

# 9. Required Metrics

Primary relevance metric: (Highly Relevant + Relevant) ÷ Total reviewed × 100.
Volume metric: total distinct matching listings available.
Secondary metrics: counts per category.
Compare directly with the existing baseline. Do not treat a raw increase in listing count as success. Do not treat precision alone as success if the result set collapses to near zero.

---

# 10. Outcome Classification

Select exactly one:

**Outcome A — MATERIAL IMPROVEMENT**: relevance improves materially AND volume remains sufficient to be useful.

**Outcome B — PRECISION IMPROVEMENT BUT INSUFFICIENT VOLUME**: relevance materially improves but total usable result set remains too small.

**Outcome C — NO MATERIAL IMPROVEMENT**: relevance does not materially improve, or performs similarly without meaningful user value.

**Outcome D — REGRESSION**: relevance worsens materially, or result volume collapses to near zero such that the discovery mechanism becomes less useful overall.

The classification must follow the actual evidence, not the preferred architecture.

---

# 11. Temporary Code Rule

If code changes are required solely to execute the experiment: keep them minimal, isolate them, document them, test them, do not commit them. After evidence collection: revert all experimental code changes, verify the revert, run the regression suite again. The repository must return to its original code state. Documentation produced may remain uncommitted pending review.

---

# 12. Testing Requirements

Run the existing backend regression suite before the experiment; run relevant targeted tests after any temporary modification; run the full backend regression suite before the final report; after reverting temporary code, run the backend regression suite again. Report exact counts.

---

# 13. Required Final Report

Create `docs/S7-APPLICATIONS-PACKAGER-IDENTITY-VALIDATION-REPORT.md` including: Hypothesis; Repository baseline; Pipeline inspection; Experiment execution (exact query: "Applications Packager"); Real provider evidence; Result inventory; Manual relevance classification; Metrics; Comparison against baseline and S5 (do not imply S5 is directly equivalent if methodologies differ); Outcome (exactly one of the four); Repository state after completion (code changes reverted Yes/No, backend tests, working tree, staged files, untracked files, commits created, tags created, push performed).

---

# 14. Interpretation Limits

Do not claim this experiment proves: that Applications Packager is the candidate's only valid career identity; that a multi-query system should be built; that multiple providers are unnecessary forever; that ranking is unnecessary forever. The experiment tests one narrower proposition only.

---

# 15. Stop Condition

After executing the experiment, manually reviewing results, calculating metrics, selecting exactly one outcome, reverting any temporary implementation, re-running regression tests, and writing the validation report:

**STOP.** Do not commit, tag, push, implement a second solution, implement multi-query discovery, add another provider, change the matcher, or build ranking.

The final response must end with:

> **STOP — S7 complete. Evidence collected, experimental code reverted and verified, no commit, no tag, no push. Awaiting Chief Architect review and next directive.**

---

## Chief Architect instruction

**Claude: execute this directive exactly as written. Treat "Applications Packager" as a controlled representation experiment, not as authorisation to redesign Job Discovery. The purpose is to isolate whether the candidate's stronger repeated Career DNA identity can improve the relevance/volume trade-off before any new architecture is considered.**
