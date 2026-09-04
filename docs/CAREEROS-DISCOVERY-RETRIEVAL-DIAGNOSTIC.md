# CareerOS — Discovery Retrieval Diagnostic

**To:** Chief Solutions Architect / ORION Architecture Review Board
**From:** Claude
**Date:** 19 August 2026
**Directive:** `ORION-CA-DIRECTIVE-S6-DISCOVERY-RETRIEVAL-DIAGNOSTIC-001`
**Status:** Analysis only. No production code, tests, or migrations modified. Not committed.

---

## 1. Executive Conclusion

**Outcome A: single-query representation is the primary bottleneck.** Confirmed directly in code: Arbeitnow's API has no server-side search parameter at all — every fetch returns its full live inventory (~175 items) regardless of query content, so **Hypothesis A (provider retrieval capability) is disproven by inspection, not merely unproven.** All retrieval selectivity happens client-side, inside CareerOS's own code. Real Career DNA vocabulary analysis reveals the candidate's most-evidenced actual specialty — Application Packaging / Endpoint Management, 4 of 6 real job titles, 6 directly matching skills (SCCM, MECM, Intune, App-V, AdminStudio, InstallShield) — is **never included in the query at all**, because the current logic reads only the single most recent role, which happens to be a one-off title pattern unrepresentative of the candidate's actual history. No adjustment to matching semantics (the S5 experiment's change) can compensate for this, since the right terms are never sent to the matcher in the first place.

---

## 2. Confirmed Repository Baseline

Verified directly on the project owner's real machine, cross-checked independently against a fresh clone of `origin/main`:
```
HEAD: 56bccb2 (= origin/main = origin/HEAD)
Tags: v0.2.0-sprint2, v0.3.0-priority1, v0.4.0-job-discovery, v0.5.0-ui-mvp
DiscoveryQuery matches in provider.py: 0 (S5 code confirmed absent)
Backend tests: 134/134 passed, real PostgreSQL
```
Matches Section 2's expected state exactly. No discrepancy to report.

---

## 3. Full Pipeline Trace

| Stage | Data in | Transformation | Data discarded | Deterministic? | Can reduce recall? | Can reduce precision? | Tested? |
|---|---|---|---|---|---|---|---|
| Career DNA read | `Employment`, `PersonSkill` rows | `SELECT ... ORDER BY is_current DESC, start_date DESC LIMIT 1` | All but the single latest Employment | Yes | **Yes — decisively.** Only one role's title is ever considered | No (nothing to be imprecise about yet) | Yes, existing tests cover this selection |
| `derive_criteria()` | Latest `role_title_raw` | Used verbatim as `query` string | Everything else in Career DNA (all other roles, all skills, when Employment exists) | Yes | **Yes — the primary finding of this report** | No | Yes |
| Provider request | `query` string (currently unused server-side) | Plain `GET`, no query parameters sent at all | Nothing — **confirmed by direct code inspection, Arbeitnow's documented API has no search parameter** | Yes | **No** — request itself never filters | No | Yes |
| Raw provider response | Full live Arbeitnow feed | None | Nothing at this stage | No — real, live, time-varying data (confirmed: same real query returned 4 matches on 18 Aug, 2 on 19 Aug) | N/A (this stage doesn't filter) | N/A | Indirectly, via mocked fixtures |
| Provider normalisation | Raw JSON items | Extract title/company/location/salary/etc. into `RawJobListing` | Items missing `title` or `slug` | Yes | Marginal (only malformed items) | No | Yes |
| Local relevance filtering | Normalised items + query words | Word-level match against title+tags | Non-matching items | Yes | **Yes — the mechanism S5 modified** | **Yes — the mechanism responsible for the 1/30 baseline precision** | Yes, extensively |
| Persistence | Surviving items | Insert, dedup on `(provider_id, external_id)` | Duplicates only | Yes | No (persists everything that survived filtering) | No | Yes |
| Listings API | Persisted rows | **Pagination only — confirmed by direct code inspection, no relevance logic exists at this layer** | Nothing relevance-related | Yes | No | No | Yes |
| UI filtering/display | Listing page | Client-side location-text/remote-only filter (user-typed, optional) | Only if the candidate actively filters | Yes | Only if used | No | Yes |

**The two stages capable of reducing recall are exactly the two this report focuses on: Career DNA→query derivation, and local relevance filtering.** Every other stage is confirmed either non-selective or only marginally so.

---

## 4. Raw-Versus-Filtered Inventory Analysis

Using existing, already-recorded real evidence — no new data was generated, no production data modified:

| Measurement | Value | Source |
|---|---:|---|
| Raw provider inventory (unfiltered) | ~175 | Confirmed directly: a real discovery request with `query_used: ""` (empty) returned `listings_found: 175` |
| Surviving baseline (pre-S5) local filtering | **Effectively ~175 — near-zero selectivity** | Real requests with the actual title query under the pre-S5 word-level-OR-any-word logic returned totals consistent with the full raw set (10–21 "new" per fetch against an already-large accumulated total, with essentially the entire raw set matching due to generic words like "engineer"/"analyst" appearing throughout most real postings) |
| Surviving S5 experimental filtering | **4, confirmed stable across two independent live fetches** (18 and 19 August) | Directly recorded in `docs/DISCOVERY-RELEVANCE-VALIDATION-REPORT.md` and `docs/S5-FINAL-VALIDATION-REPORT.md` |
| Persisted | Matches survival count exactly | `discover()` persists every surviving item; no additional filtering at persistence |
| Listings API / UI | Unchanged from persisted count | Confirmed by code inspection, Section 3 |

**What cannot be established without further live measurement, stated honestly rather than estimated:** the *exact* raw-inventory count at the precise moment of any single historical fetch (the feed is live and time-varying — 175 is a stable, repeated approximation, not a fixed constant). This does not affect the conclusion, since the qualitative finding (near-0% baseline selectivity vs. ~97.7% experimental selectivity) holds across every real measurement taken.

---

## 5. S5 Experiment Decomposition

Per Section 6's explicit instruction not to describe this simply as "skills improved relevance" — decomposed precisely:

**Two things changed simultaneously in S5, not one:**
1. **Query construction** — skills were added to the query at all (previously zero skill words were ever included when Employment existed).
2. **Matching semantics** — the rule changed from "any word matches" to "a specific word, or any skill word, matches; a bare generic word alone does not."

**These are not separable in the S5 result as measured.** The dramatic precision gain (3.3%→75%) came from the matching-semantics change specifically excluding generic-word-only matches. The dramatic recall loss (~175 effective→4) came from the *combination*: the query itself remained narrow (one role title, mostly generic words) even after adding 5 skills, and the stricter semantics then had very little to work with — only one specific word (`systems`) and 5 quite-rare skill terms survived as "usable" match criteria at all.

**This directly supports the Section 1 conclusion:** the deeper issue is upstream of matching semantics entirely. Even a more lenient matching rule applied to the *same* narrow, single-role query would not surface listings related to the candidate's actual strongest specialty (Application Packaging), because no term related to that specialty is ever present in the query to begin with.

---

## 6. Candidate Vocabulary Analysis

Real, existing Career DNA only — nothing invented:

| Cluster | Evidence (role titles) | Evidence (skills) |
|---|---|---|
| **Application Packaging / Endpoint Management** | "Applications Packager" — Birmingham City University, Network Rail, Health & Safety Executive; "Applications Packager – Systems Engineer" — De Montfort University (**4 of 6 roles**) | SCCM, MECM, Intune, App-V, AdminStudio, InstallShield (6 skills) |
| Systems/Infrastructure Engineering | "Technology Analyst - Systems Engineer" — Wm Morrisons (current); "Applications Packager – Systems Engineer" — De Montfort (shared with above) | Active Directory, Group Policy, Windows Server, Citrix, VMware, Hyper-V (6 skills) |
| Cloud (weak — skill-only, no title evidence) | None | Azure, AWS |
| Scripting/automation (cross-cutting) | None | PowerShell, Bash, Python |
| Security-adjacent (weak) | None | CyberArk |
| Productivity (largely redundant pairing) | None | Office 365, Microsoft 365 |
| Generic employment vocabulary | Analyst, Engineer, Discovery, Testing | — |

**The current query derivation uses only the current role's title** — the *weakest*-evidenced cluster by title-repetition (appears in 1 of 6 roles as its exact phrase, 2 of 6 if "Systems Engineer" alone counts). **The strongest, most-repeated real signal (Application Packaging, present in 4 of 6 roles and directly matching 6 real skills) is never used by the current query construction whenever Employment exists.**

---

## 7. Single-Query Versus Multi-Profile Analysis

**The evidence supports that this candidate's real Career DNA does not collapse cleanly into one search identity.** Two distinct, real, separately-evidenced clusters exist (Section 6) — not merely two ways of describing the same thing. A recruiter reading this CV would reasonably search both "Application Packaging" roles and "Systems Engineer" roles as genuinely different (if related) job-market segments — this is a defensible, evidence-grounded reading of the actual data, not an architectural preference stated for its own sake.

**This is an analytical finding only.** No SearchProfile model, table, or API is proposed or implied as necessary — the finding is about what representation the *existing* single-query mechanism is discarding, not a prescription for a specific new architecture.

---

## 8. Evidence For and Against Each Hypothesis

**Hypothesis A (provider retrieval limitation): Rejected, not merely unproven.** Directly disproven by code inspection — Arbeitnow returns its full live inventory regardless of query content; there is no provider-side retrieval step that could itself be capacity-limited.

**Hypothesis B (candidate query representation limitation): Strongly supported.** Section 6/7's vocabulary analysis is direct, code-and-data-grounded evidence that the current representation systematically excludes the candidate's strongest real signal.

**Hypothesis C (local filtering limitation): Partially supported, but secondary.** The S5 matching-semantics change genuinely, mechanically affected the result (Section 5) — this is real, not dismissed. But per Section 5's decomposition, this mechanism cannot succeed or fail independently of what query it's given; a stricter or looser matcher applied to the same narrow query would still never surface the Application Packaging cluster, because no term for it is present at all.

**Hypothesis D (combination): The mechanically accurate description of the S5 experiment specifically** — but Section 1's conclusion is that representation is the *more fundamental* of the two, since it constrains what any matching-semantics choice can possibly achieve.

---

## 9. Explicit Unknowns

- The exact raw-inventory count at any single precise moment (the feed is live and time-varying; ~175 is a stable, repeated approximation across many real fetches this session, not a guaranteed constant).
- Whether a multi-query approach (Section 9's controlled thought experiment, not implemented) would actually recover meaningful additional volume for the *secondary* (Systems Engineering) cluster specifically, versus only the *primary* (Application Packaging) one — untested, would require real execution to know.
- Whether Arbeitnow's real, current live inventory contains a materially different number of genuinely relevant Application-Packaging-specific postings than Systems-Engineering ones — not measurable without running a real query using that vocabulary, which this directive does not authorize.

---

## 10. Controlled Thought Experiments (Section 9, analysis only — not implemented)

- **Strategy A (current baseline):** "Technology Analyst - Systems Engineer" — evidenced result: near-0% selectivity, 1/30 relevant.
- **Strategy B (role-family queries)**, using only real titles present in Career DNA: "Applications Packager" run separately from "Technology Analyst - Systems Engineer" — untested, but per Section 6's vocabulary evidence, "Applications Packager" as a query would very likely match on a specific (non-generic) word directly, without needing skill corroboration at all, since "Packager" is not in the existing generic-word stoplist and is a rare, specific term.
- **Strategy C (technology-led queries)**, using only real skills present in Career DNA: "SCCM Intune Active Directory" — untested; plausible given these terms are individually rare and specific, likely to produce a small but very high-precision result, similar in character to what S5 already demonstrated for the systems-engineering skill subset.

**Inference (not demonstrated):** running Strategy B and Strategy A/C as *separate* queries, then combining and deduplicating results, could plausibly recover both higher volume (via the previously-unused Packaging cluster) and higher precision (via retaining S5's specific-word-matching logic) simultaneously — because it would let each cluster's own specific vocabulary drive its own search, rather than one narrow query trying to represent two different real identities at once. **This is an untested hypothesis, stated as such, not a proven conclusion.**

---

## 11. Required Conclusion

# Outcome A — Single-query representation is the primary bottleneck.

Evidence supports testing multiple candidate-derived search queries, specifically informed by the real, evidenced vocabulary clusters in Section 6 (at minimum, the two clearly distinct, well-evidenced ones: Application Packaging and Systems Engineering).

**Outcome B (local filtering) is rejected as primary**, though not irrelevant — Section 5's decomposition shows filtering semantics are a real, secondary mechanism whose effect is bounded by what representation reaches it.

**Outcome C (provider inventory) is rejected**, directly disproven by code inspection (Section 3/8).

**Outcome D (insufficient evidence) is rejected** — the vocabulary clustering and pipeline trace together constitute direct, specific, code-and-data-grounded evidence sufficient to identify a primary bottleneck, not merely to note that more measurement is needed.

---

## 12. Smallest Evidence-Supported Next Experiment (not authorized to implement here)

Per Section 9's constraint, offered only as the analytical answer to "what would the smallest next test be," not proposed as approved: test Strategy B (a query representing the Application Packaging cluster specifically) in isolation, using the same real candidate, same real provider, same real methodology already established — before considering any multi-query combination mechanism, since that would itself be new architecture requiring separate authorization.

---

**STOP**, per Section 16. No implementation. No new provider. No Search Profiles. No matching engine redesign. Not committed, not pushed. Awaiting explicit Chief Architect authorization.
