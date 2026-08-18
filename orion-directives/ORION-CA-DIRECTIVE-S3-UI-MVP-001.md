# Project ORION / CareerOS

## Chief Architect Directive — Lean CareerOS UI MVP

**Directive ID:** ORION-CA-DIRECTIVE-S3-UI-MVP-001
**Status:** AUTHORISED, IMPLEMENTED, ACCEPTED (per the Chief Architect's review of `docs/UI-MVP-REAL-VERIFICATION-COMPLIANCE-REPORT.md`, 16 August 2026)
**From:** Chief Solutions Architect
**To:** Claude — Chief Software Engineer
**Project:** ORION / CareerOS
**Scope:** Lean CareerOS UI MVP

**This is the authoritative instruction for the CareerOS UI MVP implementation.** Per the Chief Architect's explicit directory-governance guidance (16 August 2026): `/orion-governance/` holds standards/ADRs/risk/engineering controls; `/orion-directives/` holds authoritative Chief Architect instructions such as this one; `/prompts/` holds reusable/operational AI prompts. This file's presence here formalizes `/orion-directives/` as the permanent home for directives of this kind, superseding the earlier practice of storing them only under `/prompts/`.

---

## 1. Strategic Context

CareerOS has reached the point where the core backend capabilities exist:

```text
CV
 ↓
Document Intelligence
 ↓
Career DNA
 ↓
Job Discovery
 ↓
Real Job Listings
```

The next objective is **not to expand the architecture**.

The objective is to make the existing capability usable by a real candidate and determine whether CareerOS can produce its first practical outcome:

> **Can the system take a candidate's CV, understand their career history, discover relevant jobs, and present those opportunities clearly enough to support real job applications?**

This directive authorises only the minimum user interface required to test that proposition.

---

# 2. Primary Objective

Build a **lean, functional CareerOS web interface** over the existing backend.

The UI must expose the existing capabilities without redesigning, replacing, or expanding the underlying ORION architecture.

The implementation must prioritise:

1. Real usability.
2. Honest presentation of system limitations.
3. Real backend integration.
4. Minimal new architecture.
5. Fast validation of the CareerOS value proposition.

---

# 3. Product Flow

The primary user journey is:

```text
Register / Login
        ↓
Dashboard
        ↓
Upload CV
        ↓
Extract Career Information
        ↓
Review Career DNA
        ↓
Discover Jobs
        ↓
Review Relevant Opportunities
```

Do not introduce additional workflow stages unless required to make this journey functional.

---

# 4. Required UI Pages

Only the following pages are authorised.

## 4.1 Authentication

Provide:

```text
/login
```

Registration may exist as a mode or component within the login experience.

Requirements:

* Register.
* Login.
* Persist authentication.
* Logout.
* Handle authentication errors clearly.
* Do not create unnecessary account-management features.

---

## 4.2 Dashboard

The Dashboard must show a concise summary of the candidate's actual CareerOS data.

At minimum:

```text
Documents
Employment Records
Skills
Discovered Jobs
```

These must be populated from real backend data.

Do not use static demonstration counts as a substitute for API integration.

The dashboard should answer:

> **What does CareerOS currently know about me?**

And:

> **What can I do next?**

---

## 4.3 CV / Documents

Provide a page for:

```text
Upload CV
View uploaded documents
Run extraction
View extraction status
Apply extracted information
```

The UI must connect to the existing Document Intelligence APIs.

Do not build:

* A new extraction engine.
* A second storage mechanism.
* A browser-only fake extraction workflow.
* A general-purpose document management system.

The existing backend is authoritative.

---

## 4.4 Career DNA

Provide a readable view of the candidate's existing:

```text
Employment
Skills
```

The first version does not require full editing capability.

The purpose is inspection and validation.

The UI must clearly distinguish provenance.

For example:

```text
AI-extracted from your CV
Self-reported
Verified
```

Do not present AI-extracted information as though it was manually entered or independently verified.

This requirement is mandatory.

---

## 4.5 Job Discovery

Provide the existing discovery capability through the UI.

The page must support:

```text
Discover Jobs
Search query
Location
Salary preference
Remote / hybrid preference where supported by the existing API
```

The UI must use the existing Job Discovery backend.

Do not implement a new matching engine.

Do not introduce ranking algorithms.

Do not add AI job scoring.

The UI is a consumer of the existing Job Discovery capability.

---

## 4.6 Job Listings

Display real discovered listings.

At minimum:

```text
Job title
Company
Location
Remote status
Posted date where available
Salary information where disclosed
Tags
Link to original job
```

Salary honesty is mandatory.

If salary data is unavailable, the UI must say so clearly.

For example:

```text
Salary not disclosed by provider
```

The configured salary preference must not be represented as though it filtered results when the provider supplies no salary information.

---

# 5. Explicit UX Requirements

The interface should be:

* Clean.
* Minimal.
* Professional.
* Desktop-first but responsive.
* Easy to understand without documentation.

Avoid:

* Excessive dashboards.
* Complex analytics.
* Decorative architecture diagrams.
* Enterprise administration interfaces.
* Settings pages unless strictly required.
* Features designed only to demonstrate engineering sophistication.

The user should be able to understand the application within a few minutes.

---

# 6. Mandatory Honesty Requirements

CareerOS must not overstate what it knows.

The UI must accurately represent:

### CV extraction

If information was extracted by the deterministic parser:

```text
AI-extracted from your CV
```

or equivalent wording.

### Salary

If the provider does not disclose salary:

```text
Salary not disclosed
```

The configured salary preference must not be presented as evidence that a job meets that salary requirement.

### Location

Current location filtering is text-based.

Therefore, do not claim:

```text
Within 25 miles
```

unless genuine geographic radius logic exists.

If the system currently performs text matching, state that appropriately where necessary.

### Job relevance

Do not label jobs:

```text
Best Match
95% Match
Highly Recommended
```

unless a genuine authorised matching system calculates those values.

The current system is Job Discovery, not a Matching Engine.

---

# 7. Architecture Constraints

The following architecture is frozen:

```text
CareerOS UI
      ↓
CareerOS API
      ↓
Document Intelligence
      ↓
Career DNA
      ↓
Job Discovery
```

The UI must not:

* Write directly to the database.
* Bypass service layers.
* Duplicate backend business logic.
* Reimplement Career DNA logic.
* Reimplement Job Discovery logic.
* Introduce a second authentication system.

---

# 8. Explicitly Out of Scope

The following are NOT authorised:

* Matching Engine.
* Job scoring.
* Candidate-job percentage matching.
* Recruiter intelligence.
* Recruiter watchlists.
* Interview Pipeline.
* Application tracking.
* Automatic applications.
* CV generation.
* Cover-letter generation.
* General-purpose CV parsing.
* Additional job providers.
* AI agents.
* Autonomous workflows.
* Mobile application.
* Full Career DNA editing.
* General ORION platform expansion.

If any of these appear necessary, stop and report the dependency.

Do not implement them pre-emptively.

---

# 9. Frontend Technology

Use the existing frontend architecture where possible.

Before changing the frontend stack:

1. Inspect the current repository.
2. Reuse existing dependencies.
3. Reuse existing routing.
4. Reuse the current API client patterns.

Do not replace the frontend framework.

Do not introduce a component framework or state-management architecture unless the existing code genuinely requires it.

---

# 10. Implementation Order

Implement in this order:

### Stage 1 — Connectivity

Confirm:

```text
Frontend → Backend API
Authentication
Environment configuration
Docker connectivity
```

Do not proceed until real connectivity works.

---

### Stage 2 — Core Navigation

Implement:

```text
Login
Dashboard
Documents
Career DNA
Job Discovery
```

Navigation may be minimal.

---

### Stage 3 — Real Document Workflow

Implement and verify:

```text
Upload
Extract
Review status
Apply
Career DNA update
```

Use a real CV.

Do not validate this only with mocked responses.

---

### Stage 4 — Real Job Discovery

Implement:

```text
Discovery form
Real API request
Real listing display
Location filtering
Salary disclosure
Posted dates
Original job link
```

Use the live provider and real PostgreSQL where available.

---

### Stage 5 — Real Browser Verification

This stage is mandatory.

Automated tests alone are insufficient.

A real user must perform:

```text
Register/Login
Upload CV
Run extraction
Apply extracted data
Inspect Career DNA
Run Job Discovery
Inspect returned jobs
Open an original job listing
```

Record every defect found.

Fix only defects within the authorised UI MVP scope.

---

# 11. Testing Requirements

Add tests appropriate to the frontend implementation.

At minimum:

```text
Authentication flow
API connectivity
Document upload workflow
Extraction state handling
Career DNA rendering
Provenance rendering
Job discovery request
Job listing rendering
Salary honesty
Location filtering behaviour
Error handling
```

Existing backend and kernel tests must remain green.

---

# 12. Defect Discipline

If a defect is discovered:

1. Reproduce it.
2. Identify the root cause.
3. Fix the smallest correct layer.
4. Add regression coverage.
5. Re-test the real workflow.

Do not:

* Rewrite working architecture because of one UI bug.
* Introduce speculative abstractions.
* Blame external providers without inspecting the actual data.
* Replace working components without evidence.

---

# 13. Completion Criteria

The UI MVP is complete only when all of the following are true.

### Functional

A real candidate can:

```text
Login
↓
Upload a real CV
↓
Extract real data
↓
Apply data to Career DNA
↓
View employment and skills
↓
Run real Job Discovery
↓
View real job listings
↓
Open the original listing
```

### Technical

* Frontend tests pass.
* Backend tests remain passing.
* Kernel tests remain passing.
* Docker deployment works.
* Real API communication works.
* Real PostgreSQL verification is performed where applicable.

### UX

* No blank pages.
* No broken navigation.
* No hardcoded fake data presented as real.
* Clear error messages.
* Clear provenance.
* Honest salary handling.
* Honest location handling.
* Honest job relevance presentation.

---

# 14. Real Browser Gate

The following statement is prohibited until manually verified:

> **"The CareerOS UI MVP is complete."**

Completion cannot be based solely on:

```text
npm test
pytest
docker-compose up
```

A real browser session is required.

The system must be used manually.

Real defects discovered during usage must be reported.

---

# 15. Governance Requirements

Before implementation begins:

1. Save this directive as:

```text
/orion-directives/ORION-CA-DIRECTIVE-S3-UI-MVP-001.md
```

2. Commit it to the repository.

3. Confirm the repository state.

During implementation:

* Do not modify historical release tags.
* Do not rewrite `v0.3.0-priority1`.
* Do not rewrite `v0.4.0-job-discovery`.
* Maintain existing technical debt records.
* Add new technical debt only for genuine deferred issues.
* Do not classify deliberate scope exclusion as technical debt.

---

# 16. Completion Report

When finished, produce:

```text
CareerOS UI MVP — Completion Report
```

The report must include:

1. What was implemented.
2. What existing components were reused.
3. What was deliberately not built.
4. Frontend test results.
5. Backend regression results.
6. Kernel regression results.
7. Docker verification.
8. Real browser verification.
9. Defects found during real use.
10. Fixes applied.
11. Known limitations.
12. Technical debt introduced.
13. Exact repository state.
14. Recommended release decision.

---

# 17. Implementation Gate

You are authorised to implement **only this Lean CareerOS UI MVP**.

You are not authorised to begin:

* Matching Engine.
* Additional providers.
* Recruiter Intelligence.
* Interview Pipeline.
* Application automation.

When the UI MVP is complete:

**STOP.**

Produce the Completion Report.

Do not tag, push a release, or begin the next sprint until explicit Chief Architect review.

---

## Final Architectural Principle

The purpose of this UI is not to make CareerOS look complete.

The purpose is to test whether this narrow chain produces practical value:

```text
REAL CV
   ↓
REAL EXTRACTION
   ↓
REAL CAREER DNA
   ↓
REAL JOB DISCOVERY
   ↓
REAL OPPORTUNITIES
```

Everything else remains frozen until this chain is demonstrated in actual use.

---

**END OF DIRECTIVE**

---

## Fulfillment Record (added 16 August 2026, post-implementation)

Implemented, real-browser-verified, and accepted per `docs/UI-MVP-REAL-VERIFICATION-COMPLIANCE-REPORT.md`. Six real defects were found through live use (not automated tests) and fixed; 33/33 frontend, 134/134 backend, 52/52 kernel tests passing. `v0.5.0-ui-mvp` tagging is pending final working-tree confirmation, per the Chief Architect's governance action requiring the tag to cover exactly the reviewed changes.
