# CareerOS — Career Profile → Job Discovery Representation Analysis

**To:** Chief Solutions Architect / ORION Architecture Review Board
**From:** Claude
**Date:** 20 August 2026
**Directive:** `ORION-CA-DIRECTIVE-S8-CAREER-PROFILE-DISCOVERY-ANALYSIS-001`
**Status:** Analysis only. No production code modified. No tests run (baseline already confirmed multiple times across S4–S7; re-running would not add evidence, per Section 12's "do not run experiments merely to create activity").

---

## 1. Executive Conclusion

**CareerOS's Career DNA schema is significantly richer than what has ever reached Job Discovery — and richer than S4 through S7 assumed.** Confirmed by direct code inspection: a `Role` entity exists with a `seniority_level` field and an `occupation_id` link into a full `Occupation`/`JobFamily`/`Industry` taxonomy — precisely the structure that could bridge a historical CV title to modern labour-market terminology. **This entire mechanism is dormant.** `Employment.role_id` is never populated by any real code path; `Occupation`/`JobFamily`/`Industry` have zero rows, zero API surface, zero service layer. Only two things have ever reached Job Discovery for this real candidate: the raw `role_title_raw` string, and (as of S5's now-reverted experiment) up to 5 `PersonSkill` names. Everything else the schema was built to hold — structured seniority, occupation classification, `Technology`, `Competency` — exists in name only.

---

## 2. Repository Baseline

Confirmed directly on the project owner's real machine:
```
git rev-parse HEAD: 56bccb2060f922c015d5bec96418bb793d5213d4
git describe --tags --exact-match HEAD: no exact match (expected -- see below)
git tag -l: v0.2.0-sprint2, v0.3.0-priority1, v0.4.0-job-discovery, v0.5.0-ui-mvp
```

**Precise, correct relationship, not a discrepancy:** `v0.5.0-ui-mvp` tags commit `3427936` (the UI MVP implementation itself); `HEAD` sits one commit further, at `56bccb2` (the compliance report documenting that release's own tag-correction incident, committed afterward). `git describe --exact-match` correctly reports no exact match because `HEAD` and the tag are, by design, not the same commit -- confirmed via `git log --oneline --decorate`, which shows `3427936` explicitly annotated `(tag: v0.5.0-ui-mvp)` two commits back from `HEAD`. This matches every prior session record exactly; nothing has changed or drifted.

Working tree: 9 documentation files staged (the full S4-S7 record), 2 files correctly untracked (`CAREEROS-INTERVIEW-ACQUISITION-MVP-VALIDATION.md`, `JOB-DISCOVERY-POST-RELEASE-ASSESSMENT.md`), confirmed via direct `git status`/`git diff --cached` inspection, not assumed.

---

## 3. Evidence Reviewed

`DISCOVERY-RELEVANCE-VALIDATION-REPORT.md`, `S5-DISCOVERY-QUERY-ENRICHMENT-IMPLEMENTATION-REPORT.md`, `S5-FINAL-VALIDATION-REPORT.md`, `CAREEROS-DISCOVERY-RETRIEVAL-DIAGNOSTIC.md`, `S7-APPLICATIONS-PACKAGER-IDENTITY-VALIDATION-REPORT.md`, `CAREEROS-INTERVIEW-ACQUISITION-MVP-VALIDATION.md`, `JOB-DISCOVERY-POST-RELEASE-ASSESSMENT.md` — all reviewed. Current code independently re-verified rather than trusted from summary (Section 3's explicit instruction), surfacing the Role/Occupation finding above, which no prior report identified.

---

## 4. Current Career DNA Actually Available

Confirmed by direct inspection of every model file:

| Entity | Exists in schema? | Populated for real candidate? | Ever read by discovery? |
|---|---|---|---|
| `Employment.role_title_raw` | Yes | Yes — 6 real rows | Yes (sole source, pre-S4/S5) |
| `PersonSkill` | Yes | Yes — 20 real rows | Only during S5's reverted experiment |
| `Role` (seniority, occupation link) | Yes | **No — `role_id` never set** | No |
| `Occupation` / `JobFamily` / `Industry` | Yes | **No rows at all, no API, no service** | No |
| `Technology` / `PersonTechnology` | Yes | **No — not written by CV extraction** (confirmed: the extractor's real output always has `"technologies": []`) | No |
| `Competency` / `PersonCompetency` | Yes | **No — same reason** | No |
| `CareerGoal` / `LocationPreference` / `WorkPreference` / `SalaryPreference` | Yes | No — no write path exists at all (established in earlier sessions, re-confirmed unchanged) | No |

---

## 5. Current Discovery Representation Actually Used

At present (post-S7-revert, matching the published `v0.5.0-ui-mvp` state exactly): `Employment.role_title_raw` alone, verbatim, as the entire query. Nothing else.

---

## 6. Information Currently Ignored by Job Discovery

- **19 of 20 real skills** (only the current-role fallback path ever used up to 3, and that only when no Employment exists — for this candidate, who has Employment, zero skills reach discovery in the published state).
- **5 of 6 employment records** (only the single most recent is ever read).
- **The entire Role/Occupation/JobFamily/Industry structure** — dormant, as established in Section 1.
- **Employment duration, seniority progression, and role-chaining** (`previous_employment_id` exists, tracking promotions/title changes, but is never read for discovery purposes).

---

## 7. Historical Title Versus Demonstrated Capability Analysis

**These are genuinely different things, and S7 tested only the former.** "Applications Packager" is a *label* — a historical, employer-assigned job title. The candidate's *demonstrated capability* (SCCM, MECM, Intune, App-V, AdminStudio, InstallShield — real, specific, repeatedly-evidenced tools) is a different, arguably more durable signal: labour markets rename job titles over time, but the underlying tools and their names change more slowly. **S7's regression (0% relevant) tested whether the market currently uses the exact phrase "Applications Packager" — it did not test whether the underlying skills have current market value.** This distinction, which Section 5 explicitly asked to be preserved, has not been tested by any directive to date.

---

## 8. S4–S7 Evidence Synthesis

| Directive | What was actually varied | Result | What it does NOT prove |
|---|---|---|---|
| S4/Baseline | Title alone, old permissive matcher | 3.3% relevant, high volume | — |
| S5 | Title + skills, AND stricter matcher (two variables at once) | 75% relevant, volume collapsed to 4 | Cannot attribute the effect to skills alone vs. the matcher change alone — genuinely confounded, as S6 already noted |
| S6 | (analysis only) | Identified representation, not filtering or provider, as primary | — |
| S7 | Title alone, but a *different* title ("Applications Packager" instead of the most-recent role) | 0% relevant | Does not test skills at all; does not test whether the underlying capability has market value, only whether one specific historical label does |

**No directive to date has tested skills in isolation, with the matcher held constant.** This is the one clean variable-isolation that hasn't yet been run.

---

## 9. Bottleneck Assessment

Confirmed, not re-litigated: provider inventory is not the bottleneck (S6, disproven by code inspection — no server-side search parameter exists). Local filtering is real but secondary (S6). **Representation remains primary — but S8's schema inspection narrows this further: the representation problem is not merely "which existing field to read," it's that the schema's own designed solution (Role→Occupation) was never built out, leaving only two blunt instruments (raw title, raw skill list) rather than the structured classification the architecture anticipated.**

---

## 10. Options A–E Analysis

### Option A — Continue with a single historical job title
Evidence supports **not** pursuing this further: two separate single-title experiments (the current-role default, and S7's "Applications Packager") both produced poor results (3.3%, 0%) via different failure modes (over-broad generic-word matching; word-sense ambiguity). Repeating this pattern with a third title is unlikely to yield new information.

### Option B — Represent discovery using existing demonstrated skills and experience patterns
**Never actually isolated as its own experiment.** S5 tested skills *combined with* a matcher change; this option, done cleanly (skills alone, existing matcher unchanged), would be the first true test of the underlying hypothesis. Evidence for: real, specific, repeatedly-evidenced skill data already exists and is currently unused for this candidate. Unproven assumption: that skill terms alone (without any title context at all) produce results that are both relevant and sufficiently numerous. Falsifiable by: running exactly this and manually reviewing results, same as every prior directive's methodology.

### Option C — Establish current market terminology from external evidence
**This is a genuine, identified, unverified research requirement, not a proposal to implement.** No mechanism exists in CareerOS to determine whether "Applications Packager," "Endpoint Engineer," "Systems Engineer," or some other term is the current market's preferred label for this candidate's actual work. Section 7 explicitly forbids silently substituting one title for another and claiming equivalence — this option would require genuine external research (e.g., real job-market data on current title prevalence) before any implementation could be justified, and is flagged here as exactly that: a requirement, not a solved problem.

### Option D — Multiple independently evidenced career representations
Real evidence exists (Section 4/6 of the S6 diagnostic, re-confirmed here) that the candidate's Career DNA supports at least two distinct clusters (Application Packaging, Systems Engineering). **This remains an analytical finding, not an implementation proposal** — the dormant Role/Occupation structure (Section 1) suggests the schema *could* eventually support this properly, but building it now would be new architecture, explicitly out of this directive's scope.

### Option E — No representation change; provider/filtering is the actual bottleneck
**Evidence continues to reject this.** S6's code-level finding (no provider-side search parameter exists) stands unchanged and unchallenged by any S7 evidence.

---

## 11. Assumptions and Unverified Claims, Stated Explicitly

- That skill-term matching, tested in true isolation (no title, unchanged matcher), would outperform either prior single-title experiment — plausible given S5's partial signal, but genuinely untested as an isolated variable.
- That "current market terminology" differs meaningfully from the candidate's historical titles — plausible (job markets do rename roles over time) but not established by any evidence gathered in this project; would require external research per Option C.
- That the dormant Role/Occupation structure, if built out, would actually improve outcomes — entirely unverified; it's a schema capability, not evidence of effectiveness.

---

## 12. Smallest Evidence-Based Next Experiment (identified, not authorized here)

**Test Option B in true isolation:** the candidate's skill terms alone, as the entire query, with the existing (unmodified, pre-S5) matcher — the one clean variable-isolation not yet attempted across S4 through S7. This would finally separate "does skill-based representation help" from "does stricter matching semantics help," which S5 conflated.

---

## 13. Explicit Architecture Impact

None proposed. Everything in Section 12 would use fields that already exist and are already populated (`PersonSkill`) — no schema change, no new entity, no write path to Career DNA.

---

## 14. Explicitly Rejected Alternatives

Building out the Role/Occupation taxonomy (Option D-adjacent) — real, evidenced as dormant, but explicitly new architecture, out of scope here. Automatic historical-to-modern title translation (Option C's implementation) — no external research has been performed to justify it yet.

---

## 15. Recommendation

**Only where evidence supports it, per Section 11's own qualifier:** the evidence supports authorizing Option B as a clean, isolated experiment (Section 12) as the next directive's scope — not because it's guaranteed to succeed, but because it is the one remaining variable-isolation that would resolve genuine ambiguity left by S5's confounded result.

---

## 16. Proposed Next Directive Scope — Not Implementation

A directive scoped narrowly to: query = candidate's skill terms only (no title), existing unmodified matcher, same real candidate/PostgreSQL/Arbeitnow/manual-review methodology as S4–S7, same forced four-outcome classification, same temporary-code-then-revert discipline already established and proven reliable across S5 and S7.

---

## 17. Final Repository State

No files modified beyond this report's creation. No tests run (per Section 12, none were necessary to establish an already-repeatedly-confirmed baseline). Not committed, not tagged, not pushed.

---

## 18. Chief Architect Clarification — Additional Mandatory Evidence Scope

Addressing four specific questions raised after the initial report, using only evidence already confirmed this session — nothing fabricated or inferred.

### 18.1 Current professional role (Systems Engineer, Morrisons)

**Confirmed directly, not assumed:** "Technology Analyst - Systems Engineer" at "Wm Morrisons Supermarkets Ltd" exists in Career DNA, `is_current=true`, `start_date=2022-02-01`. **This is, and has always been, the exact record the production `derive_criteria()` selects** (`ORDER BY is_current DESC, start_date DESC LIMIT 1`) — confirmed by direct inspection of the unmodified, currently-published logic. **Important clarification for the record: the S4/baseline result (3.3% relevant) already tested this exact current role, not a generic "historical" title.** S7's "Applications Packager" experiment was a deliberate *departure* from this current-role baseline to test a different, more-repeated-but-not-current title — it did not replace or represent the system's normal behavior.

No employment-specific skill linkage exists in the schema (`PersonSkill` links to `Person`, not to a specific `Employment` record) — there is no way, currently, to know which of the 20 real skills were specifically used in the Morrisons role versus earlier ones. This is a real, disclosed evidence gap, not fabricated.

### 18.2 Demonstrated technical capability beyond title

Real, already-confirmed skill evidence (20 skills) genuinely spans systems engineering, infrastructure/server administration (Windows Server, Active Directory, Group Policy, VMware, Hyper-V), endpoint/application technologies (SCCM, MECM, Intune, App-V, AdminStudio, InstallShield), cloud (Azure, AWS), scripting/automation (PowerShell, Bash, Python), and security-adjacent tooling (CyberArk). **This is real evidence, not invented.**

**Stated plainly, per the explicit instruction not to fabricate:** no "AI-assisted or AI-enabled technical work" appears anywhere in the real, extracted Career DNA. PowerShell/Bash/Python are genuine, evidenced automation skills; Azure/AWS are genuine, evidenced cloud skills — but no AI-specific skill, tool, or project was ever extracted from the real CV this session. This must be reported as an absence, not inferred into existence.

### 18.3 Recent project evidence

**A distinct `Project` entity (with `ProjectTechnology`/`ProjectSkill` linking tables) exists in the schema — confirmed by direct inspection — but is entirely unpopulated and unreferenced by any service or API, the same dormancy pattern as the Role/Occupation finding in Section 1.**

**More fundamentally, and confirmed by the real extraction evidence already on record this session:** the actual CV extraction result for this candidate's real document explicitly returned `"projects": [], "achievements": []`. **This means any recent AI/automation project evidence, if it exists in the candidate's real professional life, is not currently present in Career DNA at all — not because Job Discovery or any representation logic excludes it, but because it was never extracted from the source CV document in the first place.** This is a Document Intelligence extraction-completeness question, sitting one full layer upstream of everything S4–S8 have investigated, and explicitly out of scope for implementation under every directive issued to date (Document Intelligence has been frozen throughout).

### 18.4 Recency versus historical repetition

**This session already contains one real, direct, head-to-head comparison relevant to this exact question.** The production baseline (current role, Morrisons — recency) scored 3.3% relevant. S7's deliberate test of a historically-repeated-but-not-current title ("Applications Packager," appearing in 4 of 6 roles) scored 0%. **In the one real test available, recency outperformed historical repetition.** This is offered as evidence from a single real comparison, not a general claim about which principle is always correct.

---

## 19. Required Finding

> If an employer reviewed the candidate's current CV, current Systems Engineer role, demonstrated technical skills, and recent AI/automation project work, would a Job Discovery query based only on one historical job title materially misrepresent the candidate?

# Partially — important evidence is missing but representation remains adequate.

**Reasoning, broken into its three real, distinct parts:**

1. **Title representation is not currently a problem.** The published, live system already uses the candidate's current role (Systems Engineer, Morrisons) — not a historical title. The word "historical" in this question does not describe the actual production baseline.
2. **Skills representation is a real, confirmed gap.** 20 real, evidenced skills exist and currently reach discovery in zero cases when Employment exists (the published, reverted state). This is the S8 report's existing core finding (Section 9–12), unchanged by this clarification.
3. **AI/automation project evidence is not missing from Job Discovery specifically — it is missing from Career DNA entirely, upstream at the extraction stage.** There is nothing for a representation change to include, because nothing was ever captured. Stated as a genuine, real evidence gap, not something Job Discovery is responsible for or capable of fixing.

**No implementation proposed or performed as a result of this clarification** — Sections 12/15/16 of the original report (test skill-terms-alone, in isolation) remain the recommended smallest next step; this addendum sharpens *why*, without expanding scope.

---

**STOP — S8 complete, including Chief Architect clarification (Sections 18-19). Analysis only. No implementation, no commit, no tag, no push. Awaiting Chief Architect review and next directive.**
