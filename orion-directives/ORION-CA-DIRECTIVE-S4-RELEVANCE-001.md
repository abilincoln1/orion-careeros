Give Claude the following **exact directive**. It keeps the work narrow and requires a real before/after measurement before anything else expands.

---

# Project ORION / CareerOS

## Chief Architect Directive

### Sprint 4 — Discovery Relevance Validation Experiment

**Directive ID:** `ORION-CA-DIRECTIVE-S4-RELEVANCE-001`
**To:** Claude, Chief Software Engineer
**From:** Chief Solutions Architect
**Date:** 18 August 2026

---

## 1. Authority and Context

The Post-Release Product Validation Report has been reviewed.

The current CareerOS architecture has demonstrated the following:

```text
Candidate CV
    ↓
Document Intelligence
    ↓
Career DNA
    ↓
Job Discovery
    ↓
Displayed Opportunities
```

The engineering pipeline works.

However, product validation has identified a material relevance problem.

The existing baseline review of 30 real job listings produced:

| Classification    | Baseline |
| ----------------- | -------: |
| Highly Relevant   |        0 |
| Relevant          |        1 |
| Possibly Relevant |        5 |
| Irrelevant        |       24 |
| **Total**         |   **30** |

The evidence reviewed indicates that the primary bottleneck is currently:

> **Career DNA → Discovery Criteria Construction**

Specifically, the current discovery logic derives its query primarily from:

```text
latest_employment.role_title_raw
```

while the candidate's extracted skills are not meaningfully incorporated when an Employment record exists.

The candidate already has Career DNA containing specific skills including technologies and capabilities relevant to job discovery.

Therefore, the next action is **not** to add another provider, build a Matching Engine, introduce ranking, or extend the application workflow.

The next action is a small, reversible experiment to determine whether using more of the existing Career DNA materially improves opportunity relevance.

---

# 2. Objective

Implement and validate the smallest possible change that improves:

```text
Career DNA
        ↓
Discovery Criteria
        ↓
Relevant Opportunities
```

The objective is to test the hypothesis:

> **Using selected existing candidate skills alongside the current employment role can materially improve the relevance of discovered job opportunities.**

This is a **product validation experiment**.

It is not authorisation to build a Job Matching Engine.

---

# 3. Required First Step — Inspect Before Changing

Before writing any code:

1. Inspect the current implementation of:

   * `derive_criteria()`
   * Job Discovery service
   * Arbeitnow provider
   * existing relevance filtering
   * `Employment` read paths
   * `PersonSkill` read paths

2. Confirm the current behaviour in code.

3. Confirm exactly how:

   * the employment title is used;
   * skills are currently used;
   * search terms are passed to the provider;
   * provider results are locally filtered.

4. Produce a short **Current-State Confirmation** before implementation.

Do not assume the Post-Release Validation Report remains accurate without checking the current repository state.

---

# 4. Implementation Constraint

Do **not** simply concatenate every skill into one unrestricted OR-style search string without analysing how the existing matcher will interpret it.

For example, the following must **not** be implemented blindly:

```python
query = f"{role_title} {' '.join(all_skills)}"
```

If the downstream matching logic interprets terms permissively, adding many skills could increase irrelevant matches rather than improve precision.

The implementation must preserve the distinction between:

```text
Primary Role Terms
```

and:

```text
Supporting Skill Terms
```

You may introduce a small internal structured representation if required.

For example:

```text
DiscoveryCriteria
    primary_role_terms
    supporting_skill_terms
```

This is an internal implementation detail only.

Do not create unnecessary new architecture, database tables, or public APIs.

---

# 5. Skill Selection

Do not automatically use all available skills.

Inspect the candidate's actual Career DNA and identify a limited set of skills that are likely to be discriminating for the candidate's target roles.

Generic terms should not be allowed to dominate relevance.

The skill-selection logic must be:

* deterministic;
* explainable;
* covered by tests;
* based only on existing Career DNA.

Do not introduce:

* LLMs;
* embeddings;
* vector search;
* external AI services.

---

# 6. Permitted Changes

You are authorised to modify only what is necessary to conduct this experiment.

Permitted:

1. `derive_criteria()` or its immediate equivalent.
2. Existing Job Discovery service logic.
3. Existing local relevance filtering, **only where necessary to consume structured role and skill criteria**.
4. Internal schemas or data structures required by the existing service.
5. Existing tests.
6. New focused regression tests.
7. Documentation required to record the experiment.

Schema changes require explicit justification and should be avoided unless genuinely unavoidable.

---

# 7. Explicitly Frozen

The following remain frozen.

Do not implement:

* Matching Engine;
* candidate/job scoring system;
* ranking algorithms;
* weighted recommendation engine;
* embeddings;
* vector database;
* LLM-based job analysis;
* second job provider;
* Indeed integration;
* JobServe integration;
* Totaljobs integration;
* recruiter intelligence;
* recruiter watchlists;
* application tracking;
* application workflow;
* interview pipeline;
* autonomous applications;
* geographic radius search;
* preference CRUD expansion;
* new Career DNA entities;
* new ORION Platform Kernel capabilities.

Do not broaden this directive.

If the smallest viable solution appears to require any frozen capability, **stop and report rather than expanding scope**.

---

# 8. Testing Requirements

Add tests covering, at minimum:

### A. Criteria construction

Verify that:

* an employment role remains the primary candidate signal;
* selected skills are incorporated as supporting signals;
* generic skills do not cause uncontrolled broadening;
* missing employment data still behaves correctly;
* missing skills still behaves correctly;
* existing fallback behaviour is preserved.

### B. Relevance behaviour

Test examples where:

* role terms alone match;
* meaningful skill overlap improves relevance;
* generic single-word matches do not incorrectly dominate;
* clearly unrelated jobs remain excluded.

### C. Regression

Run:

```text
Backend test suite
Frontend test suite if affected
Kernel suite if affected
```

Report exact counts.

Do not claim unchanged components were tested unless they were actually executed.

---

# 9. Real-World Validation Requirement

Automated tests are insufficient to close this experiment.

After implementation:

1. Run discovery against the real authorised Arbeitnow provider.
2. Use the real candidate's existing Career DNA.
3. Persist results through the normal CareerOS path.
4. Verify persistence against real PostgreSQL.
5. Select a fresh sample of **30 real listings**.

The new sample must be reviewed using the same classification methodology as the baseline:

```text
Highly Relevant
Relevant
Possibly Relevant
Irrelevant
```

Do not redefine the categories after implementation.

---

# 10. Required Before-and-After Comparison

Produce:

| Classification    | Baseline | Experiment |
| ----------------- | -------: | ---------: |
| Highly Relevant   |        0 |          ? |
| Relevant          |        1 |          ? |
| Possibly Relevant |        5 |          ? |
| Irrelevant        |       24 |          ? |
| **Total**         |   **30** |     **30** |

Calculate:

```text
Relevant Opportunity Rate
=
(Highly Relevant + Relevant)
/
30
```

Baseline:

```text
1 / 30 = 3.33%
```

Report the experimental result using the same calculation.

---

# 11. Guard Metric

Improved precision must not be achieved simply by returning almost no jobs.

Therefore report:

* total listings retrieved from the provider;
* total listings persisted;
* total listings surviving local relevance filtering;
* total listings available for review.

If the change materially reduces the result set, explain why.

A system returning one excellent job and nothing else must not automatically be considered successful.

---

# 12. Independent Challenge

After implementation and testing, perform a fresh review as though the work was written by another engineer.

Challenge the conclusion:

1. Did skill enrichment actually cause the improvement?
2. Could the difference be caused by changes in provider inventory?
3. Is the sample sufficiently comparable to the baseline?
4. Did the result count collapse?
5. Did the change accidentally create a ranking or matching engine beyond this directive?
6. Did the implementation introduce hidden architectural expansion?
7. Is the improvement material rather than marginal?

State clearly which conclusions are:

* **Verified**
* **Supported but limited**
* **Hypotheses**

---

# 13. Success Criteria

The experiment is considered technically complete if:

* the implementation remains within scope;
* all required automated tests pass;
* real provider execution succeeds;
* real PostgreSQL persistence is verified;
* a fresh 30-listing manual review is completed.

However:

> **Technical completion does not automatically mean product success.**

The experiment demonstrates product improvement only if the proportion of:

```text
Highly Relevant + Relevant
```

improves materially beyond the baseline:

```text
1 / 30 = 3.33%
```

The exact outcome must be reported honestly.

Do not adjust the classification criteria or sample methodology to make the result look better.

---

# 14. Required Deliverable

Produce:

```text
docs/DISCOVERY-RELEVANCE-VALIDATION-REPORT.md
```

The report must include:

1. Current-State Confirmation.
2. Hypothesis.
3. Exact implementation.
4. Files changed.
5. Test results.
6. Real provider verification.
7. PostgreSQL verification.
8. Before-and-after relevance table.
9. Result-count guard metric.
10. Independent challenge.
11. Limitations.
12. Recommendation.

Also update the relevant project validation record **only if the evidence warrants an update**.

---

# 15. Git Safety

Do not use:

```powershell
git add -A
```

Stage files explicitly.

Before any commit, run:

```powershell
git status
```

and report exactly what will be committed.

Do not:

* move existing tags;
* delete existing tags;
* rewrite history;
* force push.

---

# 16. Stop Condition

After producing the validation report:

**STOP.**

Do not:

* add another provider;
* begin application tracking;
* build ranking;
* build matching;
* start Interview Acquisition;
* expand CareerOS.

Await explicit Chief Architect review of the measured results.

The next decision will be based on evidence from this experiment.

---

## Chief Architect Principle

CareerOS will now proceed according to this sequence:

```text
Measure
    ↓
Identify the actual bottleneck
    ↓
Make the smallest evidence-based change
    ↓
Measure again
    ↓
Expand only if the evidence justifies expansion
```

**Begin with Section 3: inspect and confirm the current repository state before modifying any code.**

---

### Recommended file location

Save it as:

```text
orion-directives/ORION-CA-DIRECTIVE-S4-RELEVANCE-001.md
```

Then tell Claude to **read that file in full, commit the directive itself first only if it is not already tracked, and then begin Section 3 without implementing anything until the Current-State Confirmation is produced**.

This directive deliberately avoids committing you to a second job board or a Matching Engine before we know whether the existing Career DNA can solve the measured relevance problem.
