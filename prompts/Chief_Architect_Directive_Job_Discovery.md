Yes. Given the Priority 1 closure report, I would now authorise **Job Discovery as the next lean vertical slice**, but I would **not authorise the rest of Sprint 3** (matching, recruiter intelligence, interview pipeline, etc.) yet.

The important distinction is that Claude should first formally close/tag Priority 1, then implement only the minimum Job Discovery capability needed to produce useful job opportunities.

Use this as the directive.

---

# Project ORION / CareerOS

## Chief Architect Directive — Priority 1 Closure & Job Discovery

**To:** Claude, Chief Software Engineer
**From:** Chief Solutions Architect
**Date:** 14 August 2026
**Subject:** Formal Priority 1 acceptance and authorisation of lean Job Discovery implementation

### Directive Status

**AUTHORISED**

The Priority 1 Compliance Report has been reviewed.

The evidence presented is sufficient to accept Priority 1:

> **Real CV → real Document Intelligence → Career DNA persistence → provenance verification → real PostgreSQL verification**

The implementation may now be formally closed.

However, the project direction is deliberately changing:

> **Keep CareerOS lean. Build useful capability incrementally. Do not build infrastructure merely because the architecture allows it.**

The immediate objective is to begin generating tangible user value from the CareerOS platform.

---

# 1. Priority 1 — Formal Closure

Before beginning Job Discovery:

1. Verify the current Git state.
2. Confirm the Priority 1 changes are present.
3. Confirm the working tree is clean or explicitly report anything unexpected.
4. Confirm the current branch and remote.
5. Confirm whether the Priority 1 commit has already been pushed.
6. If not already done, create and push:

```text
v0.3.0-priority1
```

Use the exact final commit containing the accepted Priority 1 implementation.

Do **not** rewrite history.

Produce a short closure record confirming:

* commit
* tag
* remote status
* test status
* coverage
* PostgreSQL verification status

Do not make unrelated changes during this closure.

---

# 2. Job Discovery Is Now Authorised

After Priority 1 is formally closed, begin the **Job Discovery** capability.

This is the next practical CareerOS value-producing capability.

The objective is simple:

> **Take the candidate's Career DNA and discover relevant live job opportunities.**

Do not attempt to build the complete Job Intelligence Platform yet.

---

# 3. Scope — Minimum Viable Job Discovery

Implement only what is necessary to support:

```text
Career DNA
     ↓
Job Discovery
     ↓
Job Listings
     ↓
Relevant opportunities presented to candidate
```

The first usable version should be capable of:

### Candidate profile inputs

Use the existing Career DNA wherever available:

* roles
* employment history
* skills
* technologies
* competencies
* career goals
* location preferences
* work preferences
* salary preferences

Do **not** create a second candidate-profile model merely for Job Discovery.

Career DNA remains the source of truth.

---

# 4. Salary Range

The candidate's current target salary range for discovery is:

> **£40,000 – £110,000**

Design the implementation so this is a configurable CareerOS preference rather than a hard-coded application constant.

Where a job advert does not expose a salary:

* do not invent one;
* do not infer an exact salary;
* retain the listing;
* mark salary as unknown/not disclosed.

Where a salary range is provided, preserve the source value and currency.

---

# 5. Location / Work Preference

Respect the existing CareerOS preference model.

The discovery architecture must be capable of handling:

* Birmingham / West Midlands opportunities
* reasonable commuting distance
* UK remote
* UK hybrid
* London hybrid where appropriate
* broader UK opportunities where the candidate's preferences permit them

Do not hard-code these locations into the discovery engine.

Use the existing preference model where possible.

---

# 6. Job Listing Model

Create only the minimum domain model required to represent a discovered job.

At minimum consider:

* JobListing
* JobProvider / source
* title
* employer
* location
* work arrangement
* salary information
* description
* source URL
* external job identifier
* discovered timestamp
* publication timestamp where available
* expiry/status information
* raw/source metadata where necessary

Before implementing, inspect the existing Sprint 3 architecture and repository.

**Do not automatically create every entity proposed in the original Sprint 3 architecture.**

If something is unnecessary for the first usable vertical slice, defer it.

---

# 7. Provider Architecture

Use the provider abstraction already designed for Job Intelligence.

However:

> **Implement only one real provider initially unless the existing architecture makes another provider essentially free.**

Do not build a multi-provider framework with several integrations simply to demonstrate extensibility.

The provider boundary should exist, but implementation should remain minimal.

The first provider must be legally and technically usable under its published access conditions.

Do not scrape a site merely because it is technically possible.

Do not implement LinkedIn scraping.

Do not implement Indeed scraping unless an appropriate authorised/API-access route actually exists.

If a provider cannot legally or technically be integrated, document that limitation and select an alternative rather than creating a brittle workaround.

---

# 8. Discovery Behaviour

The first version should support a basic discovery request such as:

```text
Discover jobs for this candidate.
```

The system should derive appropriate search criteria from Career DNA and preferences.

At minimum, discovery should consider:

* relevant role/title
* skills
* technologies
* location
* remote/hybrid preference
* salary range

The system should return actual job listings where the provider supplies them.

---

# 9. No Matching Engine Yet

This is important.

**Do NOT build the Sprint 3 Matching Engine at this stage.**

Job Discovery and Job Matching are separate concerns.

For this phase:

```text
Discovery = find potentially relevant jobs
```

Not:

```text
Discovery + scoring + ranking + recommendation engine
```

If basic ordering is unavoidable because of provider behaviour, document it.

Do not create a sophisticated match score.

---

# 10. No Recruiter Intelligence

Do not implement:

* recruiter watchlists
* recruiter profiles
* recruiter relationship management
* recruiter intelligence
* recruiter outreach
* contact enrichment

These remain frozen.

---

# 11. No Interview Pipeline

Do not implement:

* interview tracking
* interview stages
* interview preparation workflow
* interview scheduling
* application workflow

These remain frozen.

---

# 12. No CV Expansion

Do not expand Document Intelligence.

Priority 1 is complete.

Do not turn Job Discovery into another CV parsing project.

The existing Career DNA is sufficient input for this phase.

---

# 13. Architecture Review Before Significant Implementation

Before writing substantial code:

1. Inspect the existing Sprint 3 Job Intelligence architecture.
2. Identify which parts are actually required for this MVP slice.
3. Identify anything in the existing architecture that would cause unnecessary complexity.
4. Produce a **Lean Job Discovery Implementation Plan**.
5. Explicitly list:

   * build now
   * reuse
   * defer
   * reject as unnecessary

Then proceed with implementation only within this directive's scope.

You do **not** need another lengthy architecture exercise if the existing architecture already adequately covers the required slice.

The objective is implementation, not another documentation cycle.

---

# 14. Testing Requirements

Every new behaviour must have automated tests.

At minimum test:

### Provider

* successful job retrieval
* malformed provider response
* missing salary
* missing location
* duplicate external job
* provider failure

### Persistence

* job creation
* external ID uniqueness
* provider attribution
* expiry/status handling

### Discovery

* candidate preferences converted into search criteria
* salary boundaries
* location/work-preference handling
* empty result set
* provider failure

### Security

Ensure provider data cannot bypass application ownership/security boundaries.

---

# 15. Real-World Verification

Do not stop at mocked tests.

Once the implementation is complete:

1. Run the automated test suite.
2. Run the application against PostgreSQL.
3. Perform a real discovery request.
4. Confirm actual job listings are retrieved.
5. Confirm listings persist correctly.
6. Confirm source URLs are preserved.
7. Confirm duplicate handling works.
8. Confirm the result is visible through the CareerOS API/UI if that surface is already available.

The goal is another **real vertical slice**, not a fixture demonstration.

---

# 16. Quality Gate

Job Discovery is not complete merely because the code compiles or tests pass.

The minimum acceptance bar is:

> A real CareerOS candidate profile can be used to discover real jobs, and those jobs can be persisted and retrieved reliably from PostgreSQL.

If the external provider prevents this from being verified, report the exact limitation rather than declaring success based on mocks.

---

# 17. Keep the Existing Quality Level

Do not regress the existing platform.

Before closure:

* existing tests must continue passing;
* new tests must pass;
* coverage must remain within project quality gates;
* PostgreSQL verification must pass;
* no kernel/product boundary violations;
* no direct ORM writes where the architecture requires service-layer writes;
* no undocumented architectural decisions;
* no silent provenance assumptions.

---

# 18. Governance

Continue using:

```text
/orion-governance
```

for permanent engineering governance.

Continue version-controlling Chief Architect directives.

The directive for this work should be saved as:

```text
/prompts/Chief_Architect_Directive_Job_Discovery.md
```

If the repository's current directive organisation has already established a dedicated:

```text
/orion-directives
```

directory, also place the authoritative directive there according to the project's established convention.

Do not create duplicate competing versions without documenting which is authoritative.

---

# 19. Release Package

At completion, prepare an Engineering Release Package containing:

* implementation summary
* changed files
* architecture decisions
* tests
* coverage
* PostgreSQL verification
* provider verification
* configuration integrity
* technical debt changes
* risk changes
* deferred work
* release manifest

Do not tag until the completion report has been produced and reviewed.

---

# 20. Technical Debt Discipline

Do not create technical debt entries simply because something was not built.

Only record genuine unresolved technical debt.

Clearly distinguish:

```text
Deferred by design
```

from:

```text
Technical debt
```

For example, not building Matching Engine in this phase is **scope control**, not technical debt.

---

# 21. Stage Boundaries

The following remain **FROZEN**:

```text
Matching Engine
Recruiter Intelligence
Interview Pipeline
Advanced AI matching
LLM-based CV parsing
Multi-provider expansion
Platform-wide file storage expansion
Unnecessary kernel capabilities
```

They may be revisited later based on evidence from the working Job Discovery product.

---

# 22. Product Principle

This is the governing principle for this phase:

> **Build the smallest useful capability that produces measurable candidate value.**

CareerOS should now move from:

```text
Architecture → architecture → architecture
```

towards:

```text
Working capability
      ↓
Real user interaction
      ↓
Evidence
      ↓
Expand where justified
```

Do not build infrastructure because it might be useful someday.

Build it when the product actually needs it.

---

# 23. Required Final Report

At the end of the work, provide:

### A. Implementation Summary

What was actually built.

### B. Real-World Verification

What was tested against real infrastructure and real job data.

### C. Test Results

Full test count, failures, coverage and PostgreSQL results.

### D. Provider Assessment

Provider used, access method, limitations and reliability.

### E. Architecture Assessment

What existing architecture was reused and what, if anything, had to change.

### F. Scope Control

Explicitly list what was **not** built.

### G. Technical Debt / Risks

Only genuine outstanding items.

### H. Release Recommendation

Recommend one of:

```text
APPROVE
APPROVE WITH CONDITIONS
DO NOT APPROVE
```

Do not tag the release until the Chief Architect reviews this final report.

---

## Final Instruction

**Priority 1 is now authorised for formal closure.**

**Job Discovery is authorised as the next implementation phase.**

Keep it lean.

Build one useful, real vertical slice.

Do not implement Matching, Recruiter Intelligence, Interview Pipeline, or other Sprint 3 components.

Do not expand the architecture unless the actual Job Discovery implementation proves that expansion is necessary.

**Proceed.**
