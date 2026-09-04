# CareerOS — Discovery Relevance Validation Report

**To:** Chief Solutions Architect / ORION Architecture Review Board
**From:** Claude
**Date:** 19 August 2026
**Directive:** `ORION-CA-DIRECTIVE-S4-RELEVANCE-001`
**Status:** Implemented, real-world verified, **not yet a clean success — the guard metric flagged a real, material problem.** Not committed, per Section 15's git safety requirement (staging explicit, awaiting review first).

---

## 1. Current-State Confirmation

Performed before any code was written (Section 3), via direct inspection:
- `derive_criteria()`: used only `Employment.role_title_raw`, verbatim, as the entire query whenever Employment existed. Skills were read only in the no-employment fallback branch.
- `JobProviderClient.search()`: accepted a single flat `query: str`, no structured fields.
- `ArbeitnowProvider`'s local filter: word-level OR match on any word ≥3 characters from that flat string.

Confirmed accurate; no drift from the Post-Release Validation Report.

---

## 2. Hypothesis

Using selected candidate skills alongside the employment role can materially improve opportunity relevance — tested via a structured `DiscoveryQuery` (primary role terms / supporting skill terms) with a matching rule chosen specifically to avoid the blind-concatenation trap Section 4 warned against: a **specific** (non-generic) role word, or **any** real skill-term overlap, is independently sufficient to include a listing; a bare **generic**-word-only match (e.g. "Engineer" alone, with no skill corroboration and no specific word) is excluded.

---

## 3. Exact Implementation

- `provider.py`: new `DiscoveryQuery` dataclass; `JobProviderClient.search()` signature changed to accept it instead of a flat string.
- `discovery_service.py`: `derive_criteria()` now always reads up to 5 real skills and passes them as `supporting_skill_terms` alongside `primary_role_terms` (the role title's words), regardless of whether Employment exists.
- `arbeitnow_provider.py`: local filter rewritten to the specific-OR-skill rule above, with a fixed, disclosed stoplist of 17 generic role words (`engineer`, `analyst`, `manager`, `technology`, etc.).

**One real bug found and fixed during test-writing itself, not glossed over:** the first version of the rule required a generic word to *literally co-occur* with a matching skill. A real test case ("SCCM Systems Administrator" — genuinely relevant, but never says "Engineer") exposed this as wrong. Corrected so skill overlap is independently sufficient, not merely a corroborator.

---

## 4. Files Changed

`provider.py`, `discovery_service.py`, `arbeitnow_provider.py`, `test_arbeitnow_provider.py` (rewritten for the new interface), `test_job_discovery_api.py` (fake client signature updated).

---

## 5. Test Results

**135/135 backend passed** (confirmed twice: this session's sandbox, and independently on the project owner's real PostgreSQL container). **33/33 frontend, 52/52 kernel — both actually executed, confirmed unaffected**, not assumed. Section 8's specific requirements covered: role-alone match, skill-corroborated match, generic-word non-domination, unrelated-job exclusion, empty/missing-data fallback behavior.

---

## 6. Real Provider Verification

Executed on the project owner's live stack. **One real infrastructure incident occurred mid-verification, reported here for completeness:** a Docker Desktop crash destroyed the PostgreSQL volume between the code-deployment step and the discovery test, requiring a full re-registration, re-upload, and re-extraction of the real CV before testing could continue. Recovery was verified identical to every prior run this session (`employments_applied: 6, skills_applied: 20`), confirming the extraction pipeline's reliability was not itself in question — this was a Docker/OS-level event, unrelated to any code in this directive.

**The actual discovery request**, once the real environment was restored:
```
{"provider_name":"arbeitnow","query_used":"Technology Analyst - Systems Engineer",
 "listings_found":4,"listings_new":4,"listings_duplicate":0}
```

---

## 7. PostgreSQL Verification

Confirmed directly via `psql` — 4 real rows, matching the API response exactly:

| Title | Company | Location | Salary |
|---|---|---|---|
| IT Systems and Infrastructure Engineer | Checkatrade | Moorgate London | Not disclosed |
| Systems Architect (All Genders) | Stark | Munich | Not disclosed |
| AWS Platform Engineer: Developer | Baringa | London | Not disclosed |
| (Senior) Cloud Architect | Xibix Solutions | Munich | Not disclosed |

---

## 8. Before-and-After Relevance Table

| Classification | Baseline (n=30) | Experiment (**n=4**) |
|---|---:|---:|
| Highly Relevant | 0 | 1 |
| Relevant | 1 | 2 |
| Possibly Relevant | 5 | 1 |
| Irrelevant | 24 | 0 |
| **Total** | **30** | **4** |

**Baseline Relevant Opportunity Rate:** 1/30 = 3.33%
**Experiment Relevant Opportunity Rate:** 3/4 = 75%

**This comparison is not directly valid, and is not presented as if it were.** Section 9 required a fresh 30-listing sample; the real system produced only 4 matching listings, full stop. The 75% figure is real and honestly calculated, but it describes 4 listings, not 30 — a fundamentally different, much less statistically meaningful sample.

---

## 9. Result-Count Guard Metric — the central finding

- Total listings retrieved from the provider (raw, pre-filter): not directly captured in this single response, but consistent with every prior live fetch this session (~175).
- Total surviving local relevance filtering: **4**.
- Total persisted: 4 (all new, zero duplicates — the account was freshly recreated after the data-loss incident, so no prior baseline existed to duplicate against).
- Total available for review: 4.

**The result set collapsed from Arbeitnow's real ~175-listing inventory to 4 — roughly 2.3% selectivity.** This is exactly the failure mode Section 11 anticipated: *"A system returning one excellent job and nothing else must not automatically be considered successful."* Four is not one, and all four are genuinely good — but four total opportunities is not yet demonstrably a *useful product outcome* on its own, regardless of how clean the precision looks.

**Why this happened, traced precisely:** the query's own words split into `["Technology", "Analyst", "-", "Systems", "Engineer"]`. Three of four usable words (`technology`, `analyst`, `engineer`) are in the generic stoplist; only `systems` is specific. The 5 supporting skills (in read order: SCCM, MECM, Intune, Azure, AWS) are individually rare, precise terms — real, live job titles containing them are correspondingly uncommon. The combination of "only one specific role word" and "a small set of highly specific skill words" is *more selective than intended* — precision improved dramatically, but recall collapsed alongside it.

---

## 10. Independent Challenge

1. **Did skill enrichment actually cause the improvement?** Yes, directly traceable — 3 of 4 results matched via `systems` or a skill term, not a generic word alone; the mechanism worked exactly as designed.
2. **Could the difference be caused by provider inventory changes?** Partially confounded, honestly disclosed: the real-world test happened after a full data reset, on a different day than the baseline, against Arbeitnow's live (time-varying) feed — not a controlled, identical inventory snapshot.
3. **Is the sample comparable to the baseline?** **No — this is the report's central limitation, not a minor caveat.** n=4 vs n=30.
4. **Did the result count collapse?** **Yes, materially — from ~21 new listings under the old logic to 4 under the new one**, on largely the same real query text.
5. **Did this accidentally build a ranking/matching engine?** No — the filter remains a pure boolean include/exclude, no scores, no ordering logic, confirmed by inspection.
6. **Did this introduce hidden architectural expansion?** No — `DiscoveryQuery` is an internal dataclass, no new table, no new endpoint, no new public API surface.
7. **Is the improvement material or marginal?** **Both, depending on which axis is measured** — precision improved dramatically (3.33% → 75%); volume collapsed dramatically (~21 → 4). Neither number alone tells the true story.

---

## 11. Limitations

- **Sample size invalidates a direct statistical comparison** — the honest headline of this report.
- A real infrastructure incident (Docker volume loss) interrupted verification, requiring data recovery mid-experiment; the recovery itself is verified sound, but it means this test ran on a freshly-recreated account rather than one with continuous history.
- The generic-word stoplist (17 words) is a fixed, disclosed heuristic, not empirically tuned — its exact boundary (why "systems" isn't generic but "engineer" is) is a judgment call, stated as such, not derived from data.
- Skill selection takes the first 5 skills in whatever order the database returns them — not ranked by relevance to any particular role, which may itself be contributing to the over-narrow result.

---

## 12. Recommendation

**Do not treat this as a clean pass or a clean fail.** The precision hypothesis is genuinely supported — skill-term matching does produce materially more relevant results when it fires. But the guard metric surfaced a real, unresolved problem: the current rule is too conservative in this specific case, and 4 opportunities is not yet a demonstrated product outcome.

**Smallest next step, not proposed as authorized here:** loosen the rule slightly — e.g., allow a *specific* (non-generic) role word to match *or* corroborate more permissively, or select skills with some awareness of which are more commonly represented in real job titles rather than by raw storage order. This is offered as a direction, not an implementation, per Section 16's explicit stop condition.

---

## 13. Git State

Per Section 15: no `git add -A` used. All changes remain unstaged, pending explicit review. `git status` reported (on the project owner's real repository, not this sandbox's stale clone) exact file list separately, not duplicated here to avoid presenting a possibly-stale status as authoritative.

---

**STOP**, per Section 16. No second provider, no ranking, no application tracking, no further expansion. Awaiting explicit Chief Architect review of this measured, mixed result.
