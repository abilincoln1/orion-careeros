# Project ORION / CareerOS

## Chief Architect Directive
### Job Discovery MVP — Acceptance, Closure & Controlled Next Step

**To:** Claude (Chief Software Engineer)
**From:** Chief Solutions Architect / ORION Architecture Review Board
**Date:** 14 August 2026
**Status:** AUTHORISED

---

# 1. Decision

The Job Discovery MVP Completion Report has been reviewed.

The reported implementation satisfies the intended lean vertical-slice scope:

- real JobProvider abstraction
- real Arbeitnow provider
- Career DNA-derived discovery criteria
- JobListing persistence
- provider/external-ID deduplication
- discovery and listing endpoints
- configurable salary preference range of £40,000–£110,000
- automated regression coverage
- reported verification against the live Arbeitnow API
- reported verification against real PostgreSQL
- no modification to the accepted Career DNA data
- no Matching Engine
- no Recruiter Intelligence
- no Interview Pipeline
- no second provider
- no unnecessary expansion of the existing architecture

Subject to the evidence contained in the Completion Report, the Job Discovery MVP is therefore:

> APPROVED FOR CLOSURE.

---

# 2. Release

Complete the release process.

Before tagging:

1. Confirm working tree state.
2. Confirm the intended Job Discovery changes are the only unpublished changes.
3. Confirm all automated tests pass.
4. Confirm the live PostgreSQL verification remains valid.
5. Confirm the live Arbeitnow verification remains documented.
6. Confirm no unapproved scope has entered the repository.
7. Confirm all required governance documents are updated.
8. Confirm the directive itself is committed under `prompts/`.

Then commit and push the final Job Discovery state.

Create:

`v0.4.0-job-discovery`

Push the tag to origin.

Do not rewrite or move the previously accepted:

`v0.3.0-priority1`

tag.

---

# 3. Governance Closure

Update the appropriate governance records to reflect:

> Job Discovery MVP — Accepted and Released.

The closure record must identify:

- implementation scope
- provider used
- verification environment
- test result
- known limitations
- deferred functionality
- outstanding technical debt
- release tag

Do not claim that salary filtering is operational.

The system currently has a configurable salary preference of:

£40,000–£110,000

but the authorised Arbeitnow provider does not expose salary data in the observed API payload.

Therefore:

> Salary preference exists as configuration/user preference, but salary-based filtering cannot currently be asserted as functional provider-side filtering.

Preserve this distinction in the documentation.

---

# 4. posted_at

The Completion Report identifies that Arbeitnow supplies `created_at` but the current implementation leaves `posted_at` NULL.

This is accepted as a non-blocking MVP limitation.

Do NOT expand the current sprint merely to address this unless doing so is genuinely trivial and does not disturb the accepted release state.

Record it clearly as a follow-up item.

Do not represent `posted_at` as populated when it is not.

---

# 5. Scope Freeze

The following remain explicitly OUT OF SCOPE for the Job Discovery MVP:

- Matching Engine
- candidate/job scoring
- ranking algorithms
- recruiter intelligence
- recruiter watchlists
- Interview Pipeline
- application tracking
- second job provider
- JobListingSkill
- JobListingTechnology
- company intelligence
- full Career Preference CRUD
- autonomous job applications
- LLM-based job analysis
- CV parser expansion
- general-purpose CV extraction

Do not implement any of these as part of the closure.

---

# 6. Architectural Principle

CareerOS must continue to follow this progression:

CV
 ↓
Document Intelligence
 ↓
Career DNA
 ↓
Job Discovery
 ↓
[future authorised intelligence layers]

Do not collapse these layers together.

Job Discovery must remain a consumer of Career DNA, not a modifier of Career DNA.

---

# 7. Next Development Objective

After the Job Discovery release has been successfully tagged and pushed, STOP.

Do not immediately begin the Matching Engine.

Do not infer authorisation for the next feature from this directive.

Prepare a short post-release assessment containing:

1. Current repository/tag state.
2. Current MVP capabilities.
3. Known limitations.
4. Current technical debt.
5. Recommended next smallest commercially useful capability.
6. Dependencies required before implementation.
7. Estimated implementation complexity.
8. Any architectural decisions that would need Chief Architect approval.

No implementation is authorised by that assessment.

---

# 8. Product Principle

ORION/CareerOS is now being deliberately developed as a lean product.

The objective is not to build the entire originally conceived platform before receiving user benefit.

The engineering priority is:

> Build the smallest useful capability, verify it against real data, release it, learn from it, then expand only where evidence justifies expansion.

Every future sprint should therefore answer:

- What user benefit does this add?
- What is the smallest implementation that delivers that benefit?
- What existing capability can be reused?
- What can deliberately remain out of scope?
- What real-world evidence will determine whether the next expansion is justified?

---

# 9. Commercial Target

The current CareerOS candidate-search parameters should support the intended salary range:

> £40,000–£110,000

This is the target range for discovery configuration.

However, do not claim that every discovered job falls within that range when the authorised provider does not expose salary information.

Where salary is unavailable, the system must remain explicit that salary is undisclosed rather than inventing, estimating, or inferring a salary.

---

# 10. Permanent Repository Governance

Continue maintaining:

`/orion-governance`

for engineering governance and standards.

Continue maintaining:

`/prompts`

for reusable and version-controlled engineering prompts/directives as already established.

Chief Architect directives must remain version-controlled inside the repository so that:

> the repository, not an individual AI conversation, remains the authoritative engineering record.

Do not create additional governance structures unless explicitly authorised.

---

# 11. Required Completion Report

After release, produce:

`docs/JOB-DISCOVERY-MVP-CLOSURE-REPORT.md`

The report must contain:

- final commit
- release tag
- test count
- test result
- PostgreSQL verification status
- live provider verification status
- provider limitations
- salary-data limitation
- `posted_at` limitation
- explicit out-of-scope list
- technical-debt status
- confirmation that Career DNA was not modified
- confirmation that no unauthorised Stage/feature was implemented

---

# 12. Stop Condition

Once:

1. documentation is updated,
2. tests pass,
3. repository state is clean,
4. final commit is pushed,
5. `v0.4.0-job-discovery` is pushed,
6. closure report is committed,

STOP.

Do not begin another implementation task.

Await the next Chief Architect directive.

---

## Final Authorisation

Job Discovery MVP:

> APPROVED

Release:

> AUTHORISED

Matching Engine:

> NOT YET AUTHORISED

Recruiter Intelligence:

> NOT YET AUTHORISED

Interview Pipeline:

> NOT YET AUTHORISED

Further platform expansion:

> NOT YET AUTHORISED

The next decision will be made from the released product state and real-world evidence, not from the original theoretical roadmap.