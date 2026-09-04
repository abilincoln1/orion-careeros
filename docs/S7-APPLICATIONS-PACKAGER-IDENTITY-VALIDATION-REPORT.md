# CareerOS — Applications Packager Identity Validation Report

**To:** Chief Solutions Architect / ORION Architecture Review Board
**From:** Claude
**Date:** 19 August 2026
**Directive:** `ORION-CA-DIRECTIVE-S7-IDENTITY-VALIDATION-001`
**Outcome: REGRESSION.** Not committed, per Section 15.

---

## A. Hypothesis Tested

> Using "Applications Packager" as the discovery query produces a materially more useful balance of relevance and result volume than the current discovery representation.

---

## B. Repository Baseline

Confirmed before any change:
```
HEAD: 56bccb2 (= origin/main = origin/HEAD)
Tags: v0.2.0-sprint2, v0.3.0-priority1, v0.4.0-job-discovery, v0.5.0-ui-mvp
Working tree: 7 documentation files staged (S4-S6 record), 3 files untracked
Backend: 134/134 passed
```
Matched the expected state exactly.

---

## C. Pipeline Inspection

Confirmed: no existing request override for query text existed (`DiscoveryRequest` had only `location`/`remote_only`/`salary_min`/`salary_max`). A minimal, additive `query_override` parameter was added to `derive_criteria()`, `discover()`, `DiscoveryRequest`, and the `/discover` endpoint — defaulting to `None`, byte-identical baseline behavior when unset, confirmed by a 134/134 regression pass before any real execution.

**A real deployment problem occurred and was caught and corrected mid-experiment, reported for completeness:** the first attempt at the real request returned `"query_used": "Technology Analyst - Systems Engineer"` — the *old* default — despite the override being sent. Root cause: the temporary code hadn't actually been copied to disk before the container was rebuilt (the same file-deployment pattern seen several times earlier this session). Confirmed via `Select-String`, corrected, and a genuinely fresh `--no-cache` rebuild performed before retrying.

---

## D. Experiment Execution

**Exact query used, confirmed in the real response:** `"query_used": "Applications Packager"`.

---

## E. Real Provider Evidence

**Live Arbeitnow data was successfully used** — confirmed by direct, real API response: `{"provider_name":"arbeitnow","query_used":"Applications Packager","listings_found":3,"listings_new":0,"listings_duplicate":3}`. No mocked data at any point in this evidence.

---

## F. Result Inventory

**3 total matching listings** — all 3 confirmed to be **the same job posting**, "Senior Software Engineer, Windows/Desktop Applications" at Speechify, posted separately for three offices (Berlin ×2, Frankfurt ×1). Confirmed via a precise query matching exactly what the real matcher checks (`title` + `tags` only, not description text).

---

## G. Manual Relevance Classification

| Title | Company | Location | Classification | Justification |
|---|---|---|---|---|
| Senior Software Engineer, Windows/Desktop Applications | Speechify | Berlin | **Irrelevant** | Pure software development role. "Applications" here means *software applications* (Speechify's product category), not *application packaging* (the candidate's actual IT-ops discipline). A genuine false-positive on word-sense ambiguity, not a real match. |
| Senior Software Engineer, Windows/Desktop Applications | Speechify | Frankfurt | **Irrelevant** | Same reasoning; same job, different office. |
| Senior Software Engineer, Windows/Desktop Applications | speechify | Berlin | **Irrelevant** | Same reasoning; effectively a duplicate posting. |

**Totals: 0 Highly Relevant, 0 Relevant, 0 Possibly Relevant, 3 Irrelevant.**

---

## H. Metrics

- **Primary relevance metric:** (0 + 0) / 3 = **0%**
- **Volume metric:** 3 total, but **only 1 genuinely distinct opportunity** (the same job posted three times)
- Highly Relevant: 0 · Relevant: 0 · Possibly Relevant: 0 · Irrelevant: 3

---

## I. Comparison

| | Baseline | S5 (skill-enriched) | S7 (Applications Packager) |
|---|---:|---:|---:|
| Relevant + Highly Relevant | 1/30 ≈ 3.3% | 3/4 = 75% | **0/3 = 0%** |
| Total distinct listings | 30 (sample) | 4 | **1** (3 postings, 1 real job) |

**S7 performed worse than the baseline on both axes simultaneously** — not merely a repeat of S5's volume problem. This is a distinct, more severe negative finding, not equivalent to S5's result.

---

## J. Outcome

# Outcome D — REGRESSION

Meets the directive's own explicit criterion on two independent grounds: relevance did not merely fail to improve, it worsened materially (0% vs. the already-poor 3.3% baseline), **and** the result volume collapsed to a single genuinely distinct opportunity, which is itself irrelevant — the discovery mechanism produced zero real value for this specific query.

**Root cause, stated precisely, not just the outcome:** "Applications" is a common English word with two unrelated technical senses (software application development vs. application packaging as an IT-operations discipline). A pure word-level matcher, however carefully tuned on generic-vs-specific term classification (as S5's logic was), has no mechanism to distinguish word senses — only word presence. This is a finding about the *matching mechanism's fundamental limits*, not a failure of the underlying S6 diagnostic's premise (that Application Packaging is a real, strongly-evidenced identity in this candidate's Career DNA) — the identity itself remains real; this particular single-word representation of it was not.

---

## K. Repository State After Completion

```
Code changes reverted: Yes -- confirmed via a fresh clone of origin/main (56bccb2),
  zero query_override occurrences, 134/134 tests passed on that clean target
Backend tests: 134/134 (pending final confirmation on the project owner's real machine)
Working tree: reverted code changes; 7 previously-staged S4-S6 documentation files
  and this new S7 report remain
Commits created: 0
Tags created: 0
Push performed: No
```

---

**STOP — S7 complete. Evidence collected, experimental code reverted and verified, no commit, no tag, no push. Awaiting Chief Architect review and next directive.**
