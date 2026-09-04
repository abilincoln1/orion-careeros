Claude’s report establishes one important result:

**The query-enrichment hypothesis failed the MVP success criteria and was correctly reverted.**

The evidence is actually useful:

* Old logic: about **30 results**, but only **1/30 relevant or highly relevant**.
* Enriched logic: only **4 total results**, but **3/4 relevant or highly relevant**.
* Therefore, the experiment exposed a **precision–recall trade-off**.
* The attempted solution was too restrictive for the current provider/search mechanism.
* The reverted baseline remains healthy: **134/134 backend tests passing**.

## What Claude should do next

Do **not** tell Claude to immediately try another query tweak.

The correct next step is to analyse the evidence and identify whether the next bottleneck is:

> **provider retrieval capability vs local filtering/matching capability**

The previous experiment changed two conceptual things at once in the retrieval pipeline: it enriched the candidate representation and introduced restrictive skill-overlap semantics. The result tells us that stricter retrieval can produce high-quality jobs, but not enough volume. It does **not yet prove** what the optimal next implementation should be.

I would give Claude an **analysis-only directive** first.

---

# Exact directive to give Claude

````markdown
# ORION-CA-DIRECTIVE-S6-DISCOVERY-RETRIEVAL-DIAGNOSTIC-001

**Project:** ORION / CareerOS  
**To:** Engineering Assistant  
**From:** Chief Solutions Architect  
**Date:** 19 August 2026  
**Status:** AUTHORISED — ANALYSIS ONLY  
**Implementation authority:** NONE

---

## 1. Purpose

The Discovery Query Enrichment experiment authorised under:

`ORION-CA-DIRECTIVE-S5-DISCOVERY-QUERY-ENRICHMENT-001`

has completed with an explicit Outcome C:

**REGRESSION — implementation reverted, baseline restored.**

The experiment produced an important but incomplete result:

- the previous discovery logic produced sufficient volume but very poor relevance;
- the experimental logic produced substantially higher relevance but insufficient volume;
- therefore the experiment exposed a precision-versus-recall trade-off.

No new implementation is authorised under this directive.

The purpose of this directive is to determine, from the existing code and real validation evidence, where the retrieval bottleneck actually exists before authorising another change.

---

# 2. Mandatory starting state

Before performing any analysis:

1. Confirm the working tree state.
2. Confirm `HEAD`.
3. Confirm the current release baseline.
4. Confirm that the S5 experimental implementation is absent.
5. Run the existing backend regression suite.

Record the exact outputs.

Expected baseline is the reverted known-good Job Discovery implementation with:

- 134/134 backend tests passing;
- no S5 experimental query-enrichment code remaining;
- no uncommitted experimental source changes.

Do not modify files in order to obtain this state.

If the repository differs materially from this baseline, STOP and report the discrepancy.

---

# 3. Core question

Determine which of the following explanations is best supported by the evidence:

### Hypothesis A — Retrieval limitation

The provider/search mechanism is fundamentally unable to retrieve a sufficiently large pool of relevant opportunities for the candidate.

### Hypothesis B — Candidate query representation limitation

The system is retrieving from an adequate inventory, but the current representation of the candidate's career profile is too broad or too narrow.

### Hypothesis C — Local filtering limitation

The provider can supply useful opportunities, but CareerOS's local filtering logic creates the poor precision/recall trade-off.

### Hypothesis D — Combination

More than one stage materially contributes to the observed result.

Do not select a hypothesis merely because it appears architecturally attractive.

Every conclusion must be tied to code inspection or previously recorded real execution evidence.

---

# 4. Required pipeline trace

Trace the complete current discovery pipeline.

At minimum document:

```text
Career DNA
    ↓
derive_criteria()
    ↓
Provider request
    ↓
Raw provider response
    ↓
Provider normalisation
    ↓
Local relevance filtering
    ↓
Persistence
    ↓
Listings API
    ↓
UI filtering/display
````

For every stage identify:

1. What data enters the stage.
2. What transformation occurs.
3. What data is discarded.
4. Whether the transformation is deterministic.
5. Whether the stage can reduce recall.
6. Whether the stage can reduce precision.
7. Whether the existing tests exercise the behaviour.

Do not change the pipeline.

---

# 5. Specific diagnostic requirement: raw inventory versus filtered inventory

The previous validation established that the final result quality is poor under the baseline and too small under the experimental logic.

This directive requires determining exactly where opportunities disappear.

Using existing code and, where safely possible, existing persisted real data:

For the same candidate criteria, determine separately:

1. Number of listings returned by the provider.
2. Number surviving provider-side/client-side search handling.
3. Number surviving CareerOS relevance filtering.
4. Number persisted.
5. Number returned by the listings endpoint.
6. Number visible after UI filtering.

If exact historical data cannot be reconstructed without modifying production data, do not fabricate numbers.

Instead identify precisely what evidence is available and what cannot be established from the current state.

---

# 6. Mandatory comparison with S5 evidence

Use the existing evidence from the reverted S5 experiment.

The known observations are:

### Baseline

* approximately 30 manually reviewed listings;
* 0 Highly Relevant;
* 1 Relevant;
* 5 Possibly Relevant;
* 24 Irrelevant.

### Experimental enrichment

* 4 total listings across two independent live runs;
* 1 Highly Relevant;
* 2 Relevant;
* 1 Possibly Relevant;
* 0 Irrelevant.

Analyse exactly what changed between these two retrieval paths.

Do not describe the experiment simply as:

> "skills improved relevance."

That conclusion is incomplete.

Determine whether the observed collapse in volume resulted from:

* query construction;
* token matching semantics;
* skill requirements;
* provider request behaviour;
* client-side filtering;
* or a combination.

This distinction is mandatory.

---

# 7. Candidate vocabulary analysis

Inspect the candidate's existing Career DNA.

Classify the available terms into categories such as:

* role titles;
* core technologies;
* infrastructure technologies;
* cloud technologies;
* endpoint-management technologies;
* generic employment vocabulary;
* generic technical vocabulary.

Do not invent new skills.

Determine whether the candidate's existing Career DNA naturally forms multiple distinct job-search profiles rather than one combined search identity.

For example, the analysis may identify separate evidence-supported clusters such as:

* Systems Engineering;
* Application Packaging;
* Endpoint Management;
* Infrastructure Support;
* Cloud Support.

These are examples only.

Do not assume these clusters are valid until verified from the actual Career DNA.

No implementation is authorised from this analysis.

---

# 8. Search-profile question

Determine whether the current architecture incorrectly assumes that:

```text
one candidate
=
one discovery query
```

Evaluate, based strictly on the candidate's existing Career DNA and employment history, whether a more evidence-supported model would instead be:

```text
one candidate
=
multiple legitimate search profiles
```

Important:

This is an analytical question only.

Do not create:

* new database tables;
* SearchProfile models;
* new APIs;
* UI changes;
* matching engines;
* ranking systems.

The purpose is only to determine whether the current single-query assumption is itself the bottleneck.

---

# 9. Controlled thought experiments

Without changing production code, evaluate the likely behaviour of at least three evidence-based retrieval strategies using the actual candidate vocabulary already present.

Examples may include:

### Strategy A — Current baseline

```text
latest role title
```

### Strategy B — Role-family queries

```text
Technology Analyst
Systems Engineer
Application Packager
Endpoint Engineer
```

Only use titles or terms actually supported by Career DNA.

### Strategy C — Technology-led queries

```text
SCCM
Intune
Active Directory
```

Again, only if those terms genuinely exist in the candidate's data.

The objective is not to implement these strategies.

The objective is to determine whether combining multiple narrower searches could theoretically avoid the observed:

```text
high volume + low relevance
```

versus:

```text
high relevance + near-zero volume
```

problem.

Clearly distinguish:

* demonstrated evidence;
* inference from the existing evidence;
* untested hypotheses.

---

# 10. Architectural constraints

The following remain frozen:

* Matching Engine
* candidate/job scoring
* ranking algorithms
* recruiter intelligence
* recruiter watchlists
* Interview Pipeline
* application workflow
* autonomous applications
* second job provider
* JobListingSkill
* JobListingTechnology
* company intelligence
* general ORION expansion
* LLM-based job analysis
* CV parser expansion

Do not implement any of these.

---

# 11. Second-provider rule

Do not add, investigate for implementation, integrate, or configure a second provider.

However, the analysis may state whether the existing evidence is sufficient or insufficient to conclude that a provider limitation exists.

The distinction is:

> You may diagnose whether provider inventory appears to be the bottleneck.

You may not solve that question by implementing another provider.

---

# 12. Required deliverable

Produce:

```text
docs/CAREEROS-DISCOVERY-RETRIEVAL-DIAGNOSTIC.md
```

The report must contain:

1. Executive conclusion.
2. Confirmed repository baseline.
3. Full pipeline trace.
4. Raw-versus-filtered inventory analysis.
5. S5 experiment decomposition.
6. Candidate vocabulary analysis.
7. Single-query versus multi-profile analysis.
8. Evidence for and against each bottleneck hypothesis.
9. Explicit unknowns.
10. Smallest evidence-supported next experiment.

---

# 13. Required conclusion format

The final recommendation must choose exactly one of:

### Outcome A — Single-query representation is the primary bottleneck

Evidence supports testing multiple candidate-derived search queries.

### Outcome B — Local filtering is the primary bottleneck

Evidence supports testing a narrower change to filtering semantics.

### Outcome C — Provider inventory is the primary bottleneck

Evidence supports reconsidering the provider limitation.

### Outcome D — Evidence is insufficient

No implementation should proceed until a specific missing measurement is obtained.

The conclusion must state why the other outcomes were rejected or remain unproven.

---

# 14. Testing

Run the existing regression suite before and after the analysis.

Expected result:

```text
134/134 backend tests passing
```

No new production tests are required because no production code is authorised.

If documentation changes cause no code changes, do not inflate test counts.

---

# 15. Git restrictions

You may create the diagnostic report.

You may NOT:

* modify production code;
* modify tests;
* modify database migrations;
* alter existing tags;
* commit;
* push;
* create a new tag.

The report remains uncommitted pending Chief Architect review.

---

# 16. Stop condition

After producing:

```text
docs/CAREEROS-DISCOVERY-RETRIEVAL-DIAGNOSTIC.md
```

and completing the required baseline verification:

**STOP.**

Do not implement the recommended next experiment.

Do not redesign Job Discovery.

Do not add a provider.

Do not create Search Profiles.

Do not create a matching engine.

Do not commit.

Do not push.

Await explicit Chief Architect authorisation.

```

## Why this is the appropriate next step

The evidence currently supports **neither “add another provider” nor “keep tweaking the matcher” as a proven next move**.

The S5 experiment uncovered a more fundamental question:

> **Is the problem that CareerOS is trying to represent a multi-dimensional career history with one search query?**

Your CV contains evidence of multiple technical identities—systems engineering, application packaging, endpoint management, infrastructure/cloud-related work—but the current system appears to collapse that into one discovery query. The failed enrichment experiment may therefore be evidence that **one large combined query is the wrong unit of retrieval**.

However, that is still a hypothesis. The directive above forces Claude to prove or reject it before writing more code.

**I would send Claude exactly that directive next.** 
```
