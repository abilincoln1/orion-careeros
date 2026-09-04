# CareerOS — Discovery Query Enrichment: Final Validation Report

**To:** Chief Solutions Architect / ORION Architecture Review Board
**From:** Claude
**Date:** 19 August 2026
**Directive:** `ORION-CA-DIRECTIVE-S5-DISCOVERY-QUERY-ENRICHMENT-001`
**Outcome: REGRESSION.** Implementation reverted, revert verified. Not committed, per Section 13.

---

## Design Analysis (Section 3), Restated

- **Current behaviour:** confirmed via direct code inspection, unchanged from the prior report — `derive_criteria()` used only the raw title string; skills were unused whenever Employment existed.
- **Skill selection:** bounded at 5, deterministic database read order, no invented ranking signal.
- **Query semantics:** independent-token OR matching; a specific primary word or any skill overlap independently sufficient; a bare generic word alone insufficient — the change specifically targeted "broader just because it's longer" without actually broadening the generic-word case.

## Implementation, Tests, Real Execution

Implemented exactly as designed (`DiscoveryQuery`, `provider.py`/`discovery_service.py`/`arbeitnow_provider.py`, rewritten test files). **135/135 backend passed, confirmed independently on real PostgreSQL twice** — once at initial verification, once again in this final clean run, isolated from the earlier data-loss recovery.

**Two independent, real, live discovery requests, on two separate days, same real Career DNA, same query:**

| Run | `listings_found` | `listings_new` | Real matches, cumulative |
|---|---:|---:|---:|
| First (18 Aug) | 4 | 4 | 4 total |
| Second (19 Aug, this final run) | 2 | 0 (both already-known) | Still 4 total |

Both real, live Arbeitnow requests against the same real, correctly-derived query (`"Technology Analyst - Systems Engineer"` + 5 real skills) returned a **small, consistent, non-growing set** — not a one-off fluctuation.

## Before/After Validation

| Metric | Before (old logic) | After (new logic) |
|---|---:|---:|
| Highly Relevant | 0 | 1 |
| Relevant | 1 | 2 |
| Possibly Relevant | 5 | 1 |
| Irrelevant | 24 | 0 |
| Highly Relevant + Relevant | 1/30 ≈ 3.3% | 3/4 = 75% |
| Total results available | 30 (sample of a larger pool) | **4 — confirmed the entire result set, not a sample, across two separate live runs** |

## Result: REGRESSION

Per the directive's own explicit Outcome C definition — *"results... collapse to near zero"* — stated as an independent trigger, not conjunctive with quality also degrading. **Real volume collapsed from ~21 matches under the prior logic to 4, confirmed stable (not growing) across two separate live runs on two separate days.** This meets the stated criterion.

**Stated for the record, not to soften the verdict:** this is not a quality regression — the surfaced listings are genuinely stronger (3.3% → 75% relevance rate on the listings that did appear). But the directive's own definition of Outcome C does not require quality to also worsen; volume collapse alone qualifies, and two independent real data points confirm it is real and persistent, not a transient fluctuation.

## Revert — Performed and Verified

Per Section 9's Outcome C instruction, **the implementation has been reverted.** The three modified source files and two test files are reverted to their exact state at `origin/main`'s last confirmed tag (`v0.5.0-ui-mvp`, commit `56bccb2`) — verified by direct comparison against a fresh clone of that exact commit, not reconstructed from memory. **134/134 backend tests confirmed passing on this reverted baseline**, matching the exact known-good pre-experiment count.

**No second redesign has been attempted in this directive**, per the explicit instruction.

## Architectural Impact

Confirmed: no frozen capability was implemented at any point (no second provider, no ranking, no schema change, no Career DNA write path) — and now, with the revert, none remains in the codebase at all.

## Recommendation

None offered beyond the revert itself, per the directive's explicit scope. The real, honest evidence gathered — that skill-overlap matching genuinely improves precision but the current calibration is too conservative for this candidate's specific skill/title combination — remains available in the prior reports for whatever the Chief Architect decides is the appropriate next, separately-authorized step, if any.

---

**STOP.** Reverted, verified, not committed, not tagged, not pushed. Awaiting the Chief Architect's next directive.
