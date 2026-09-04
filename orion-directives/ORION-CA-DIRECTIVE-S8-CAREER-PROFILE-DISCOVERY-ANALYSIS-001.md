Give Claude the following. This should be **analysis only**. Do not authorise another implementation experiment yet.

# Project ORION / CareerOS — Chief Architect Directive

**Directive ID:** `ORION-CA-DIRECTIVE-S8-CAREER-PROFILE-DISCOVERY-ANALYSIS-001`
**To:** Claude, Engineering Assistant
**From:** Chief Solutions Architect / ORION Architecture Review Board
**Date:** 20 August 2026
**Subject:** Career Profile → Job Discovery Representation Analysis

---

## 1. Authority and Purpose

You are authorised to perform an **analysis-only investigation** into the gap identified by Directives S4 through S7.

The purpose is to determine why CareerOS successfully extracts and stores a candidate's employment history and skills but currently fails to use the full body of that evidence effectively during Job Discovery.

The central question is:

> **How should CareerOS represent a candidate's evidenced skills and experience for Job Discovery without prematurely implementing a matching engine, ranking engine, or new general-purpose architecture?**

This directive does **not** authorise implementation.

---

# 2. Current Published Repository State

The last published release remains:

```text
HEAD: 56bccb2
origin/main: 56bccb2
Release tag: v0.5.0-ui-mvp
```

No existing release tag may be moved, rewritten, deleted, or altered.

S4–S7 investigation documentation may exist as staged or untracked evidence. Their presence must be verified before analysis.

Run:

```powershell
git status
git status --short
git diff --cached --stat
git diff --cached
git rev-parse HEAD
git describe --tags --exact-match HEAD
```

Do not assume the expected working-tree state is correct.

Do not run:

```powershell
git add -A
git commit -am
```

No commit, tag, push, or implementation is authorised.

---

# 3. Evidence That Must Be Reviewed

Review the actual evidence from the completed investigation, including where present:

```text
docs/DISCOVERY-RELEVANCE-VALIDATION-REPORT.md
docs/S5-DISCOVERY-QUERY-ENRICHMENT-IMPLEMENTATION-REPORT.md
docs/S5-FINAL-VALIDATION-REPORT.md
docs/CAREEROS-DISCOVERY-RETRIEVAL-DIAGNOSTIC.md
docs/S7-APPLICATIONS-PACKAGER-IDENTITY-VALIDATION-REPORT.md
docs/CAREEROS-INTERVIEW-ACQUISITION-MVP-VALIDATION.md
docs/JOB-DISCOVERY-POST-RELEASE-ASSESSMENT.md
```

Also inspect the actual current code for:

* Career DNA models;
* Employment records;
* PersonSkill records;
* any Technology, Tool, Competency, or related entities that genuinely exist;
* `derive_criteria()`;
* discovery service;
* provider;
* local relevance filtering;
* request schemas and API surface.

Do not rely only on previous reports. Verify the current implementation directly.

---

# 4. Established Evidence — Do Not Rewrite History

The following findings must be treated as evidence already gathered, subject to verification against the reports and current code:

### Current/latest-role representation

The broad title-based representation produced approximately:

```text
30 reviewed
Highly Relevant: 0
Relevant: 1
Possibly Relevant: 5
Irrelevant: 24
```

This provided volume but poor precision.

### S5 skill-enriched experiment

Adding a bounded set of real skills to the title produced:

```text
Highly Relevant: 1
Relevant: 2
Possibly Relevant: 1
Irrelevant: 0

3/4 = 75% Highly Relevant + Relevant
```

However, the total result set collapsed to four listings and was classified according to the directive's criteria as insufficiently useful/regressive.

### S7 Applications Packager identity experiment

The exact query:

```text
Applications Packager
```

returned three records representing one genuinely distinct opportunity.

The distinct opportunity was classified as irrelevant.

Outcome:

```text
Outcome D — REGRESSION
```

This experiment tested the **exact historical market label**, not the value or relevance of the underlying technical experience.

---

# 5. Critical Distinction to Analyse

The analysis must distinguish between:

```text
Historical job title
```

and:

```text
Underlying demonstrated capabilities
```

For example, do not assume that failure of an exact historical title as a search term means that the candidate's underlying skills have no current market value.

The analysis must determine, from the actual Career DNA:

1. Which skills and technologies are genuinely evidenced.
2. Which experience patterns are repeated across employment history.
3. Which capabilities appear central versus incidental.
4. Which data CareerOS already possesses but currently ignores during discovery.
5. Whether the problem is primarily:

   * candidate representation;
   * query construction;
   * local filtering;
   * terminology mismatch;
   * provider inventory;
   * or some combination.

Do not invent capabilities not present in the actual Career DNA.

---

# 6. Core Analysis Question

Trace the current pipeline:

```text
CV
↓
Document Intelligence
↓
Career DNA
↓
Candidate representation used by Job Discovery
↓
Provider inventory
↓
Local filtering
↓
Persisted Job Listings
↓
Displayed Opportunities
```

Identify exactly where information is being lost or ignored.

The analysis must answer:

> **CareerOS knows what the candidate has done and what skills they possess. Which of that information actually reaches Job Discovery, and which does not?**

Provide evidence from code and real Career DNA.

---

# 7. Market Terminology Boundary

Do **not** assume that historical CV job titles are automatically suitable modern job-search terms.

However, this directive does not authorise Claude to invent modern role titles based on intuition.

If determining current labour-market terminology requires external evidence, identify that explicitly as an **unverified research requirement**.

Do not silently substitute:

```text
Applications Packager
```

with another title and claim equivalence without evidence.

---

# 8. Architecture Boundary

The following remain forbidden:

* implementation of multi-query discovery;
* combining multiple queries;
* ranking;
* scoring;
* weighting algorithms;
* skill-overlap matching;
* a second provider;
* JobServe;
* Totaljobs;
* Indeed;
* new database tables;
* schema changes;
* new Career DNA entities;
* Document Intelligence changes;
* Career DNA write-path changes;
* application tracking;
* interview pipeline functionality;
* autonomous applications;
* LLM-generated search queries;
* general-purpose multi-identity architecture.

This directive is **analysis only**.

---

# 9. Required Options Analysis

Based strictly on evidence, identify the smallest plausible next steps.

At minimum analyse:

### Option A — Continue with a single historical job title

Assess whether evidence supports further testing.

### Option B — Represent discovery using existing demonstrated skills and experience patterns

Analyse what this would actually mean using data already present.

Do not implement it.

### Option C — Establish current market terminology from external evidence

Identify what research would be required before CareerOS could translate historical experience into current job-search terminology.

Do not perform or implement automatic translation unless separately authorised.

### Option D — Multiple independently evidenced career representations

Analyse whether the candidate's actual Career DNA supports more than one distinct representation.

Do not implement multi-query discovery.

### Option E — No representation change

Assess whether evidence instead points to provider inventory or local filtering as the primary bottleneck.

---

# 10. Critical Challenge

For every option, answer:

1. What exact evidence supports it?
2. What assumption remains unproven?
3. What problem does it address?
4. What evidence would falsify it?
5. What is the smallest possible experiment required to test it?
6. Does that experiment require new architecture?
7. Does it risk conflating:

   * skills;
   * historical titles;
   * modern market terminology;
   * and candidate preference?

Do not recommend an option merely because it is technically elegant.

---

# 11. Required Deliverable

Create:

```text
docs/S8-CAREER-PROFILE-DISCOVERY-ANALYSIS.md
```

The report must contain:

1. Executive conclusion.
2. Repository baseline.
3. Evidence reviewed.
4. Current Career DNA actually available.
5. Current discovery representation actually used.
6. Information currently ignored by Job Discovery.
7. Historical title versus demonstrated capability analysis.
8. S4–S7 evidence synthesis.
9. Bottleneck assessment.
10. Options A–E analysis.
11. Assumptions and unverified claims.
12. Smallest evidence-based next experiment.
13. Explicit architecture impact.
14. Explicitly rejected alternatives.
15. Recommendation, if and only if supported by evidence.
16. Proposed next directive scope — **not implementation**.
17. Final repository state.

---

# 12. Testing

Because this directive is analysis-only:

* Do not modify production code.
* Do not rebuild containers merely to create activity.
* Do not run experiments.
* You may run existing tests only if needed to establish that the analysed baseline is functioning.

If tests are run, record the exact result.

---

# 13. Stop Condition

After:

1. inspecting the repository;
2. reviewing the S4–S7 evidence;
3. inspecting the actual Career DNA and discovery pipeline;
4. completing the options analysis;
5. writing `docs/S8-CAREER-PROFILE-DISCOVERY-ANALYSIS.md`;

**STOP.**

Do not implement the recommended experiment.

Do not modify discovery logic.

Do not add a provider.

Do not commit.

Do not tag.

Do not push.

The final response must end exactly:

> **STOP — S8 complete. Analysis only. No implementation, no commit, no tag, no push. Awaiting Chief Architect review and next directive.**

---

## Chief Architect Instruction

**Claude: the purpose of S8 is to determine how much of the candidate's existing Career DNA is actually being used for Job Discovery, and whether the failure of individual job-title experiments reflects a deeper candidate-representation problem. Do not solve that problem yet. Establish the evidence, identify the smallest justified next experiment, and stop.**
