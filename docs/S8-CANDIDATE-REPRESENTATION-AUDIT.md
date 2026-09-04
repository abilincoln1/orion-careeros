# CareerOS — Candidate Representation Audit

**To:** Chief Solutions Architect / ORION Architecture Review Board
**From:** Claude
**Date:** 20 August 2026
**Directive:** `ORION-CA-DIRECTIVE-S8-CANDIDATE-REPRESENTATION-AUDIT-001`
**Status:** Analysis and evidence collection only. No production code, schema, or Career DNA modified.

---

## 1. Repository Baseline

Confirmed fresh, directly on the project owner's real machine (not assumed from any prior session state):
```
HEAD: 56bccb2060f922c015d5bec96418bb793d5213d4
git describe --tags --exact-match HEAD: no exact match (expected -- v0.5.0-ui-mvp tags commit
  3427936, one commit before HEAD; this relationship is by design, established and explained
  in the prior S8 report, unchanged here)
Staged: 13 documentation files (the full S4-S8 record, including this report and its directive)
Untracked: 2 files (CAREEROS-INTERVIEW-ACQUISITION-MVP-VALIDATION.md, JOB-DISCOVERY-POST-RELEASE-ASSESSMENT.md)
  -- unchanged, correctly still excluded from this investigation's scope
Working tree: clean otherwise -- zero code changes
```

---

## 2. Candidate Employment Evidence

All 6 real, persisted `Employment` records, direct inspection:

| Role Title | Employer | Start | End | Current | Description Stored? |
|---|---|---|---|---|---|
| Technology Analyst - Systems Engineer | Wm Morrisons Supermarkets Ltd | 2022-02-01 | — | **Yes** | **No — `description` is `null`** |
| Applications Packager – Systems Engineer | De Montfort University | 2020-10-01 | 2022-05-01 | No | No — `null` |
| Applications Discovery & Testing | Dell – Johnson Matthey | 2020-03-01 | 2020-10-01 | No | No — `null` |
| Applications Packager | Birmingham City University | 2016-03-01 | 2019-12-01 | No | No — `null` |
| Applications Packager | Network Rail | 2015-01-01 | 2016-01-01 | No | No — `null` |
| Applications Packager | Health & Safety Executive | 2012-01-01 | 2014-01-01 | No | No — `null` |

**Repeated role pattern:** "Applications Packager" (exact or compound form) appears in 4 of 6 records. **Most recent role:** confirmed current, Morrisons, "Technology Analyst - Systems Engineer."

**Stated explicitly, not inferred:** no responsibility or description text is stored for any employment record — the `description` field exists in the schema and is `null` for all 6 real rows. No responsibilities have been inferred to fill this gap.

---

## 3. Candidate Skills Evidence

All 20 real, persisted `PersonSkill` records, categorized by evidenced domain (categories are descriptive groupings for this audit, not a stored classification field):

| Domain | Evidenced Skills |
|---|---|
| Endpoint / Application Management | SCCM, MECM, Intune, App-V, AdminStudio, InstallShield |
| Infrastructure | Active Directory, Group Policy, Windows Server, Citrix, VMware, Hyper-V |
| Cloud | Azure, AWS |
| Automation/Scripting | PowerShell, Bash, Python |
| Cybersecurity | CyberArk |
| Productivity | Office 365, Microsoft 365 |
| **AI** | **None evidenced — zero AI-specific skill, tool, or framework appears in persisted data** |
| Networking | None evidenced as a distinct skill (Active Directory/Group Policy are identity/policy infrastructure, not networking specifically) |

`Skill` is a genuinely **structured** entity (`name`, `normalized_name`, `skill_type` enum) — not free text, not merely embedded inside a CV blob. This is a real, positive finding: the underlying data quality is good; the gap (established in the prior S8 report) is in Job Discovery's *consumption* of it, not the data's structure or existence.

---

## 4. Technology/Tool Evidence

Per the directive's explicit framing (structured / implicit-in-skills / CV text / not persisted):

- **Structured, explicitly persisted:** all 20 skills above — genuinely structured `PersonSkill` rows, not implicit.
- **Named in the directive as examples, checked against real data:** SCCM/MECM ✓ persisted. Intune ✓ persisted. Active Directory ✓ persisted. PowerShell ✓ persisted. Windows infrastructure ✓ persisted (Windows Server, Group Policy). AWS ✓ persisted. **Docker: not persisted. Python is persisted; FastAPI, PostgreSQL are not persisted. Automation platforms beyond scripting languages: not persisted. AI/LLM technologies: not persisted.**
- **Not persisted anywhere in CareerOS, despite being real and demonstrable** (see Section 6 for the distinction): Docker, FastAPI, PostgreSQL, Git/GitHub workflow discipline, React/TypeScript, prompt-based AI-collaborative software engineering.

---

## 5. Current Systems Engineer Representation

Directly answering each sub-question:

- **Represented in Employment:** Yes — confirmed current, most recent record.
- **Represented in extracted skills:** No direct linkage exists — `PersonSkill` is linked to `Person`, not to a specific `Employment` record, so there is no structural way to say which skills belong to the Morrisons role specifically versus earlier roles.
- **Represented elsewhere:** No.
- **Available to Job Discovery:** Yes — the title is available and is, in fact, already the exact value `derive_criteria()` selects by default (confirmed by direct inspection of the unmodified production logic: `ORDER BY is_current DESC, start_date DESC LIMIT 1`).
- **Actually consumed by Job Discovery:** Yes, for the title alone, in the current published (`v0.5.0-ui-mvp`) state. Not for any associated skill, since no employment-specific skill link exists.

**The candidate's current role is not missing or unrepresented — it is the one piece of representation that already works correctly.**

---

## 6. Automation and AI Evidence — Three Categories, Not Collapsed

**1. Persisted CareerOS evidence:** PowerShell, Bash, Python (automation/scripting); Azure, AWS (cloud). No AI-specific entry.

**2. Evidence available elsewhere in the repository:** None — the `orion-careeros` repository is the software itself, not a record describing the candidate's own skills.

**3. Evidence known from project work but not represented in CareerOS — real and substantial:** This same conversation, and the separately-tracked NDIP platform (per this project's own memory record: *"Collaborative AI architecture model: Claude as Chief Engineering AI, ChatGPT as Chief Solutions Architect"*), constitute genuine, demonstrable, real evidence of AI-collaborative software engineering — directing multi-stage engineering work (database design, API implementation, containerized deployment, real infrastructure debugging, Git discipline) across two real platforms (CareerOS and NDIP), using AI systems as engineering collaborators. **This is real. It is also completely absent from CareerOS's own persisted Career DNA** — no `Project`, `PersonTechnology`, or `Achievement` record exists for any of it, confirmed by the dormancy already established in the prior S8 report.

---

## 7. Project Evidence

Confirmed by direct schema inspection: a `Project` entity exists (with `ProjectTechnology`/`ProjectSkill` linking tables) but has zero rows, zero service layer, zero API — entirely dormant, same pattern as `Role`/`Occupation`.

- **NDIP:** Real, per this project's own memory record. **Not persisted in CareerOS** (Category 3, Section 6).
- **CareerOS itself:** Real, directly observable across this entire session. **Not persisted in CareerOS** (Category 3) — a notable irony: the software cannot describe its own construction as evidence of its builder's capability.
- **AI/automation implementations generally:** Same status — real, not persisted.

**No project records were added. This is inspection only, per the directive's explicit instruction.**

---

## 8. Career Preference Status

Re-confirmed unchanged from every prior session finding: `CareerGoal`, `LocationPreference`, `WorkPreference`, `SalaryPreference` exist as schema-only models. **Zero service layer, zero API route exists for any of them** (confirmed directly: `find app -iname "*preference*" -not -path "*models*"` returns nothing). They are not operational in any sense — not read, not writable, not consumed anywhere.

---

## 9. Source-to-Consumption Map — Mandatory Table

| Evidence | Exists? | Persisted? | Read by Discovery? | Used in Query? | Used in Filtering? |
|---|---|---|---|---|---|
| Current role title (Morrisons) | Yes | Yes | Yes | **Yes** | Yes (as the query itself) |
| Prior 5 employment records | Yes | Yes | Selected from, not used | No | No |
| Employment descriptions | No | No (`null`) | N/A | No | No |
| 20 real skills | Yes | Yes | Only if Employment absent | **No** (when Employment exists — the published state) | No |
| Role→Occupation taxonomy | Yes (schema) | **No rows** | No | No | No |
| Technology/Competency entities | Yes (schema) | **No rows** | No | No | No |
| Project entity | Yes (schema) | **No rows** | No | No | No |
| AI/automation project work (real, external) | N/A — not a CareerOS entity at all | No | No | No | No |
| Career Preferences (all 4 types) | Yes (schema) | No rows, no write path | No | No | No |

---

## 10. Representation Gap Analysis

- **Is Job Discovery effectively representing only one job title?** Yes, currently — but it is the *correct*, *current* title, not an arbitrary historical one.
- **Are skills being ignored?** Yes, entirely, in the published state.
- **Is current Systems Engineer experience represented?** Yes, for the title; no, for any associated skill detail.
- **Is automation experience represented?** Partially — PowerShell/Bash/Python exist as skills but are never read by discovery in the published state.
- **Is AI experience represented?** No — genuinely absent from persisted Career DNA, not merely unused.
- **Is project evidence represented?** No — dormant schema, zero rows, zero real project captured anywhere in CareerOS.
- **Are Career Preferences actually operational?** No — confirmed non-functional at every layer.
- **Which evidence already exists but is unused?** The 20 real skills — the single largest, most concrete, already-actionable gap.
- **Which relevant evidence does not exist in CareerOS at all?** AI/automation project work, employment descriptions/responsibilities, occupation classification, employment-to-skill linkage.

---

## 11. Candidate Capability Domains — Evidence-Derived, Not Job Titles

| Domain | Supporting Evidence | Stored in CareerOS? | Consumed by Discovery? | Confidence |
|---|---|---|---|---|
| Endpoint / Application Management | 6 skills (SCCM, MECM, Intune, App-V, AdminStudio, InstallShield); 4 of 6 employment titles | Yes | No | High — direct, repeated, structured evidence |
| Infrastructure / Systems Engineering | 6 skills (AD, Group Policy, Windows Server, Citrix, VMware, Hyper-V); current + 1 prior title | Yes | Title only | High |
| Cloud Engineering | Azure, AWS (2 skills, no dedicated title evidence) | Yes | No | Medium — real but thin, skill-only |
| Technical Automation | PowerShell, Bash, Python (3 skills) | Yes | No | Medium |
| Applied AI / AI-Collaborative Engineering | This session, NDIP's own memory record | **No — not persisted anywhere in CareerOS** | No | **Low confidence for CareerOS purposes specifically — real as a fact, but entirely unrepresented in the system being evaluated** |

No employability or market-demand claim is made for any domain — per the directive's explicit instruction, confidence here describes evidence strength only.

---

## 12. Outcome Classification

# Outcome B — Existing Evidence Is Partially Sufficient

**Exact evidence supporting this, not a default or hedge:** real, structured, substantial evidence exists for two clusters (Endpoint Management, Infrastructure Engineering) that Job Discovery does not currently consume — this alone would justify testing (Outcome A territory, if it were the whole picture). But genuine, material gaps also exist that no representation change alone can fix: no employment description text was ever extracted; the Role/Occupation/Project/Preference structures are entirely dormant with zero rows; and the candidate's real, substantial AI-collaborative engineering work (this project itself, NDIP) has no representation in CareerOS at all — not because discovery ignores it, but because nothing in the system has ever captured it. **Both things are true simultaneously**, which is precisely what distinguishes Outcome B from either A or C.

---

## 13. What Job Discovery Currently Represents

The candidate's current job title alone, correctly selected, verbatim.

## 14. What CareerOS Demonstrably Knows But Does Not Use

19 of 20 real skills (when Employment exists); 5 of 6 employment records beyond the most recent.

## 15. What Relevant Information Is Missing From CareerOS Entirely

Employment descriptions/responsibilities; occupation/seniority classification; any project record, including this platform's own construction and NDIP; employment-to-skill linkage; functional Career Preferences.

## 16. Smallest Possible Next Validation Question

Given Outcome B's finding that real, unused evidence exists (skills) *and* real, missing evidence exists (project/AI work) simultaneously — the smallest next validation question is narrower than either S5 or S7 attempted: **does the skills evidence that already exists, tested in true isolation from any title and from any matcher change, produce a materially better result than the current single-title baseline?** This tests only what CareerOS already has, deferring any question about the missing AI/project evidence (which would require Document Intelligence or new Career DNA work, both out of scope here) to a later, separately-evidenced decision.

---

## 17. Repository State

Confirmed via the same fresh gate check as Section 1: zero code, schema, or Career DNA changes. Only this report and its directive were added, both now correctly staged (13 total staged documentation files). Not committed, not tagged, not pushed.

---

**STOP — S8 complete. Candidate representation audited, no implementation performed, no commit, no tag, no push. Awaiting Chief Architect review and next directive.**
