Give Claude the following **exact directive**. It incorporates the evidence from the Post-Release Product Validation Report and keeps the change deliberately narrow.

---

# Project ORION / CareerOS — Chief Architect Directive

**Directive ID:** `ORION-CA-DIRECTIVE-S5-DISCOVERY-QUERY-ENRICHMENT-001`
**From:** Chief Solutions Architect
**To:** Claude, Engineering Assistant
**Status:** AUTHORISED — implementation and verification permitted within the scope below.

## 1. Authority and purpose

The Post-Release Product Validation Report has been reviewed.

The evidence identifies the current primary product bottleneck as:

> **Candidate Representation → Discovery Query Construction**

The current discovery mechanism derives its query primarily from:

```text
latest_employment.role_title_raw
```

while the candidate's existing Career DNA skills are largely unused whenever employment history exists.

The next authorised action is therefore **not**:

* adding another job provider;
* building a ranking engine;
* adding application tracking;
* expanding ORION;
* creating new Career DNA entities;
* modifying Document Intelligence.

The authorised change is to test whether the existing Career DNA can produce materially better Job Discovery results when it is used more effectively.

---

# 2. Authorised implementation

Modify the existing discovery criteria construction so that, when a latest Employment record exists, the discovery criteria incorporates:

1. the latest employment `role_title_raw`; and
2. a bounded selection of the candidate's existing `PersonSkill` names.

The existing title-only query is therefore no longer the sole representation of the candidate.

Conceptually:

```python
query = build_discovery_query(
    role_title=latest_employment.role_title_raw,
    skills=selected_person_skills,
)
```

The exact implementation may differ, but it must remain:

* deterministic;
* explainable;
* bounded;
* testable;
* based exclusively on existing Career DNA data.

**Do not simply concatenate an unlimited number of skills into one uncontrolled string without analysing how the existing provider and matcher consume the query.**

Before implementation, inspect the complete discovery flow and determine precisely how the constructed query is subsequently used by:

1. `derive_criteria()`;
2. `ArbeitnowProvider`;
3. provider-side filtering, if any;
4. client-side relevance filtering;
5. persistence and deduplication.

The implementation must address the actual execution path, not merely change a string superficially.

---

# 3. Required design analysis before code changes

Before editing code, establish and document:

### A. Current behaviour

Confirm from the current code:

* how `role_title_raw` is selected;
* how `PersonSkill` records are currently read;
* whether skill ordering exists;
* how many skills are available for the real candidate;
* how the final query is consumed by the existing matching logic.

### B. Skill selection

Determine a bounded strategy for selecting skills.

Do **not** assume that all 20 skills should automatically be included.

The strategy must answer:

* How many skills are included?
* In what order?
* Are generic skills excluded?
* Are duplicate or near-duplicate terms removed?
* Does the existing model provide enough evidence for ordering?

If the current data model does not support a principled ranking of skills, use a simple deterministic rule and state that limitation explicitly.

Do not invent proficiency, importance, recency, or relevance data that Career DNA does not contain.

### C. Query semantics

Determine whether the existing discovery flow treats the query as:

* one literal phrase;
* independent tokens;
* OR conditions;
* AND conditions;
* title/tag matching;
* some combination of the above.

The enriched query must not accidentally make the result set **broader** merely because it contains more words.

This is critical.

The implementation objective is improved candidate representation and precision, not simply generating a longer string.

---

# 4. Mandatory architectural constraint

Career DNA remains the source of candidate representation.

The architecture remains:

```text
CV
 ↓
Document Intelligence
 ↓
Career DNA
 ↓
Discovery Criteria Construction
 ↓
Job Provider
 ↓
Relevance Filtering
 ↓
Persisted Job Listings
 ↓
UI
```

Job Discovery may **read** existing Career DNA.

It must not:

* write to Career DNA;
* modify Employment;
* modify PersonSkill;
* alter extraction provenance;
* create a shortcut around the existing service boundaries.

No new database table is authorised unless a previously undiscovered technical necessity makes the authorised change impossible without one.

If that occurs:

**STOP and report. Do not expand scope unilaterally.**

---

# 5. Explicitly out of scope

The following remain frozen:

* second job provider;
* JobServe;
* Totaljobs;
* Indeed integration;
* LinkedIn integration;
* job scraping;
* ranking engine;
* scoring engine;
* semantic/vector matching;
* LLM job analysis;
* AI agents;
* recruiter intelligence;
* application tracking;
* interview pipeline;
* application automation;
* new Career DNA entities;
* preference CRUD;
* geographic radius search;
* ORION Kernel expansion;
* CV parser expansion.

Do not implement adjacent improvements simply because the relevant files are open.

---

# 6. Tests required

Add or update tests covering at minimum:

### Query construction

1. Employment exists + skills exist.
2. Employment exists + no skills exist.
3. No employment + skills exist.
4. No employment + no skills exist.
5. Skill count exceeds the selected bound.
6. Duplicate skills.
7. Generic or excluded terms, if the implementation introduces such exclusion.
8. Existing title-only behaviour remains valid as a fallback where enrichment data is unavailable.

### Regression protection

The implementation must not break:

* existing Job Discovery;
* deduplication;
* `posted_at`;
* salary honesty;
* location filtering;
* the existing word-level relevance behaviour unless a specific change to that logic is separately justified and authorised.

Run the full affected backend suite.

Do not report only newly added tests.

---

# 7. Real execution requirement

Automated tests alone are insufficient.

After implementation and automated testing, execute the real flow against:

* the real candidate's existing Career DNA;
* real PostgreSQL;
* the live authorised Arbeitnow provider.

Use the same candidate and, as far as practically possible, the same validation methodology used in:

```text
CAREEROS-INTERVIEW-ACQUISITION-MVP-VALIDATION.md
```

and the baseline established in:

```text
JOB-DISCOVERY-POST-RELEASE-ASSESSMENT.md
```

The baseline to beat is:

```text
30 listings reviewed

Highly Relevant: 0
Relevant:        1
Possibly Relevant: 5
Irrelevant:      24
```

Primary baseline:

```text
Highly Relevant + Relevant = 1 / 30 ≈ 3.3%
```

---

# 8. Measurement rules

After implementation, collect a fresh sample of up to 30 real results and classify them using the **same categories and criteria as the baseline**.

Do not change the classification methodology after seeing the results.

Report:

| Metric                     |   Before | After |
| -------------------------- | -------: | ----: |
| Highly Relevant            |        0 |     ? |
| Relevant                   |        1 |     ? |
| Possibly Relevant          |        5 |     ? |
| Irrelevant                 |       24 |     ? |
| Highly Relevant + Relevant |     1/30 |     ? |
| Total results available    | baseline |     ? |

Also report the actual queries/criteria used before and after, sufficiently clearly to allow reproduction.

Do not claim success based solely on:

* more listings returned;
* fewer listings returned;
* provider response counts;
* automated tests passing.

The primary evidence is **manual relevance quality**.

---

# 9. Interpretation rules

There are three possible outcomes.

### Outcome A — Material improvement

If Highly Relevant + Relevant increases materially while the result set remains usable:

Report the evidence.

Do not automatically proceed to another feature.

Stop for Chief Architect review.

### Outcome B — No material improvement

If the relevance ratio remains broadly similar:

Do not add another provider or ranking engine.

Report the result honestly.

The negative result itself is useful evidence.

Stop.

### Outcome C — Regression

If results become significantly worse, collapse to near zero, or become demonstrably broader and less relevant:

Revert the implementation.

Verify the revert.

Report the failure and evidence.

Do not attempt a second redesign in the same directive.

---

# 10. Important constraint: isolate the variable

This directive is an experiment.

Do **not** simultaneously:

* enrich the query;
* change word matching;
* introduce weighted matching;
* alter location logic;
* add a provider;
* change the UI.

Only one material variable should change:

> **How existing Career DNA is converted into discovery criteria.**

Otherwise, the validation result cannot be attributed to the change.

---

# 11. Required inspection of the existing validation documents

Before implementation, read the relevant validation documents in full and preserve their methodology:

* `docs/CAREEROS-INTERVIEW-ACQUISITION-MVP-VALIDATION.md`
* `docs/JOB-DISCOVERY-POST-RELEASE-ASSESSMENT.md`
* `docs/CAREEROS-POST-RELEASE-PRODUCT-VALIDATION-REPORT.md`, if present under the final repository naming used by the project.

Do not rely on summaries alone where the original classification criteria are available.

---

# 12. Required implementation report

When complete, provide a report containing:

### A. Exact problem confirmed

The exact code path that produced the previous title-only query.

### B. Change made

Files changed and the deterministic skill-selection rule.

### C. Tests

New tests, regression tests, and full-suite results.

### D. Real execution

Evidence from:

* real Career DNA;
* live provider;
* real PostgreSQL.

### E. Before/after validation

The 30-listing comparison.

### F. Result

One of:

* **MATERIAL IMPROVEMENT**
* **NO MATERIAL IMPROVEMENT**
* **REGRESSION**

### G. Architectural impact

Explicit confirmation that no frozen capability was implemented.

### H. Recommendation

A recommendation only.

Do not begin a new phase automatically.

---

# 13. Governance and stop condition

Do not:

* tag;
* create a release;
* push a release tag;
* begin another MVP stage;
* add another provider;
* implement ranking;
* implement application tracking;

without a new explicit Chief Architect directive.

A local implementation commit may be prepared only after successful verification and after the exact changed scope has been reviewed.

**Do not commit, push, or tag until the implementation report is submitted for review.**

---

# 14. Definition of success

Success is **not** "the code works."

Success is evidence that the smallest identified intervention improves the candidate's opportunity quality.

The question being tested is:

> **Does using the candidate's existing Career DNA skills in discovery criteria materially improve the proportion of genuinely relevant job opportunities compared with the existing title-only baseline?**

Implement, test, execute, measure, and report.

Then stop.

**End of Directive.**

---

One important correction to the original recommendation: I would **not authorise Claude to simply do**:

```python
query = f"{role_title} {' '.join(top_skill_names)}"
```

without first checking the downstream matching semantics. Your existing system previously had a problem where word-level OR matching became too broad. Adding 20 skill words blindly could actually make that worse. The directive above forces Claude to inspect that before changing anything.
