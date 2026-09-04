# CareerOS — Discovery Query Enrichment: Implementation Report

**To:** Chief Solutions Architect / ORION Architecture Review Board
**From:** Claude
**Date:** 19 August 2026
**Directive:** `ORION-CA-DIRECTIVE-S5-DISCOVERY-QUERY-ENRICHMENT-001`
**Status:** Not re-implemented from scratch — see the note below. Not committed, per Section 13.

---

## A note before the report itself, stated plainly

**This exact experiment — the same hypothesis, the same architectural constraints, the same isolation-of-variable requirement — was already implemented, tested, and real-world verified under `ORION-CA-DIRECTIVE-S4-RELEVANCE-001`**, completed immediately before this directive arrived. All real code changes, tests, and live evidence already exist, currently staged but uncommitted (per that directive's own stop condition). Re-implementing from nothing would duplicate real work already done and, more importantly, would violate the "isolate the variable" principle both directives share — a second implementation attempt risks changing something incidental between runs, making the two results harder to compare honestly.

**What follows maps that real, already-gathered evidence into this directive's exact required report structure (Section 12 A–H)**, including the Outcome A/B/C classification (Section 9) that the earlier report didn't frame in those specific terms — that classification is new analysis, not previously stated this way.

---

## A. Exact Problem Confirmed

Confirmed via direct code inspection before any change: `derive_criteria()` set `query = latest_employment.role_title_raw` and stopped — no skill incorporation whenever an Employment record existed. `JobProviderClient.search()` accepted only a flat string, with no structured distinction available to the matcher between primary and supporting terms.

---

## B. Change Made

- `provider.py`: new `DiscoveryQuery` dataclass (`primary_role_terms`, `supporting_skill_terms`), replacing the flat `query: str` parameter in the `JobProviderClient` Protocol.
- `discovery_service.py`: `derive_criteria()` now always reads up to 5 real `PersonSkill` names (deterministic — whatever order the existing query returns; not ranked, not invented, exactly matching Section 3B's requirement to state the limitation explicitly rather than fabricate an ordering signal Career DNA doesn't contain) and passes them as `supporting_skill_terms` alongside the role title's words as `primary_role_terms`.
- `arbeitnow_provider.py`: local matching rule — a **specific** (non-generic) primary word, or **any** supporting-skill-term overlap, is independently sufficient to include a listing. A fixed, disclosed 17-word generic-role stoplist (`engineer`, `analyst`, `manager`, `technology`, etc.) prevents a bare generic word from matching alone. **This directly addresses Section 3C's core warning** — the enriched query does not simply broaden the OR-pool; it narrows what a generic word alone can match, while giving specific words and real skills independent, non-diluted matching power.

**One real bug found and corrected during test-writing, not glossed over:** the first version required a generic word to *literally co-occur* with a matching skill for inclusion. A real test case exposed this as wrong — a listing genuinely relevant via skill overlap alone (never repeating the candidate's generic job-title words) was incorrectly excluded. Corrected so skill overlap is independently sufficient.

---

## C. Tests

**135/135 backend** (confirmed twice — this session's sandbox, and independently on the project owner's real PostgreSQL). **33/33 frontend, 52/52 kernel — both actually executed and confirmed unaffected**, not assumed unaffected. Section 6's specific scenarios covered: employment+skills, employment+no-skills, no-employment+skills (unchanged fallback), skill-count bound (limit 5), generic-word non-domination, unrelated-job exclusion, existing dedup/`posted_at`/salary-honesty/location-filter regression protection all re-confirmed passing, not newly re-tested in isolation.

---

## D. Real Execution Evidence

Real Career DNA (`finaltest2@example.com`, 6 employments, 20 skills — re-verified after a genuine, disclosed Docker Desktop data-loss incident mid-verification, recovery confirmed identical to every prior run: `employments_applied: 6, skills_applied: 20`). Real live Arbeitnow call. Real PostgreSQL persistence, confirmed via direct `psql` query, not the API response alone.

**Actual query used:** `primary_role_terms` derived from `"Technology Analyst - Systems Engineer"`; `supporting_skill_terms`: `SCCM, MECM, Intune, Azure, AWS` (first 5, database read order).

---

## E. Before/After Validation

| Metric | Before | After |
|---|---:|---:|
| Highly Relevant | 0 | 1 |
| Relevant | 1 | 2 |
| Possibly Relevant | 5 | 1 |
| Irrelevant | 24 | 0 |
| Highly Relevant + Relevant | 1/30 ≈ 3.3% | 3/4 = 75% |
| Total results available | 30 (sampled from a larger set) | **4 (the entire result set — not a sample)** |

**Stated as plainly as possible: the "after" figure is not a 30-listing sample of a larger pool — 4 was the total number of listings the new logic returned at all.** The classification methodology (Highly Relevant / Relevant / Possibly Relevant / Irrelevant, same criteria) was preserved unchanged, per Section 8's requirement — but applying it to n=4 instead of n=30 is a materially different kind of evidence, and this report does not present the 75% figure as directly comparable to the 3.3% baseline without that caveat attached every time it's cited.

---

## F. Result — Outcome Classification

**None of Sections 9's three outcomes fits cleanly, and forcing one would misrepresent the evidence:**

- Not **Outcome A** (material improvement, result set remains usable) — precision improved dramatically, but 4 total opportunities is not demonstrably a *usable* product outcome on its own; the directive's own Section 8 language ("do not claim success based solely on... fewer listings returned") and the guard-metric reasoning from the S4 directive both caution directly against this reading.
- Not **Outcome B** (no material improvement) — plainly wrong; 3.3% → 75% is not "broadly similar."
- **Closest to Outcome C** (regression via volume collapse) **on the specific "collapse to near zero" language** — real listings dropped from ~21 (under the old, too-permissive logic, on largely the same query) to 4. This is a genuine, material volume collapse, even though *quality per surfaced listing* improved rather than degraded — the opposite of what Section 9's other Outcome-C language ("demonstrably broader and less relevant") describes.

**Honest conclusion: this is a genuine mixed result the three-category framework doesn't cleanly capture** — real evidence for the underlying hypothesis (skill overlap does improve relevance when it fires), and real evidence that the current calibration is too conservative (it fires too rarely). Per Section 9 Outcome C's explicit instruction ("do not attempt a second redesign in the same directive"), **no further code change has been made in pursuit of a fix** — this is reported as the stopping point, not worked around.

---

## G. Architectural Impact

**Confirmed: no frozen capability was implemented.** No second provider, no ranking/scoring (the filter remains pure boolean include/exclude), no new Career DNA entity, no schema change, no write path from Job Discovery back into Career DNA (confirmed by inspection — `derive_criteria()` only ever reads `Employment`/`PersonSkill`). `DiscoveryQuery` is an internal dataclass, not a new public API.

---

## H. Recommendation

**Given Section 9's explicit "do not attempt a second redesign in the same directive," this report does not propose a fix.** It recommends only that the Chief Architect decide, with this real evidence in hand, between two honest paths: (1) revert to the pre-S4 logic, accepting the original 3.3% baseline as the current known state, or (2) authorize a distinct, separately-scoped follow-up directive to calibrate the skill-selection/matching rule (e.g., a larger skill count, or excluding highly rare/narrow skill terms from the "any overlap" test) — explicitly not decided here, per the isolate-the-variable discipline both directives share.

---

**STOP**, per Section 13. Not committed, not tagged, not pushed. The five code/test files and this report remain staged-but-uncommitted on the project owner's machine, awaiting explicit direction.
