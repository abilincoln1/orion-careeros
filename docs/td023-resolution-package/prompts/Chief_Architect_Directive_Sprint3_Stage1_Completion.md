# Project ORION

## Chief Architect Directive — Sprint 3 Stage 1 Completion

### Resolve TD-023 Before Stage 2

---

# Project ORION

## Chief Architect Directive

### Sprint 3 — Stage 1 Completion

### Document Intelligence Engine

**To:** Claude (Chief Software Engineer)

**From:** Chief Solutions Architect

**Date:** 2026-08-06

---

## Directive

Your Stage 1 Compliance Report has been reviewed.

The report demonstrates that:

* Storage architecture is complete.
* Provider abstraction is complete.
* Domain model is complete.
* Migration strategy is complete.
* Testing is complete.
* PostgreSQL verification has been completed.
* Coverage remains above project quality gates.

However, your own report correctly identifies one architectural blocker.

TD-023 is not merely technical debt.

It is an architectural correctness issue.

The project must never knowingly write incorrect provenance into Career DNA.

Your decision not to bypass the existing service layer and not to mislabel AI-generated data is accepted as correct engineering judgement.

Accordingly:

**Stage 1 is NOT closed.**

It is:

> **Approved with Conditions**

exactly as stated in your compliance report.

---

# Objectives

Resolve TD-023.

Complete Stage 1.

Produce a genuinely complete Document Intelligence Engine.

Do **not** begin Stage 2.

---

# Engineering Tasks

## 1.

Review the entire Career DNA write pipeline.

Document every location where provenance is written, inferred, validated or consumed.

This includes, but is not limited to:

* Person
* Employment
* Skills
* Technologies
* Competencies
* Education
* Certifications
* Projects
* Achievements
* Evidence
* References

---

## 2.

Produce a design proposal.

Present every viable solution.

For each option include:

Advantages

Disadvantages

Migration impact

Backward compatibility

Security implications

Future AI implications

Future human-edit implications

Future multi-provider implications

---

## 3.

Recommend one solution.

Do not implement until the recommendation is complete.

---

## 4.

If the preferred solution requires schema evolution:

Design it.

Prepare migrations.

Prepare service changes.

Prepare API changes.

Prepare tests.

Do not implement until approved.

---

## 5.

If the preferred solution requires service evolution:

Document every affected service.

Show why the change preserves Sprint 2 guarantees.

Demonstrate that:

* validation remains enforced
* ownership remains enforced
* provenance remains enforced
* no direct ORM writes occur

---

## 6.

If the preferred solution introduces a new architectural decision:

Write a new ADR.

---

## 7.

Update:

* Technical Debt
* Risk Register
* Architecture diagrams
* Engineering Release Package

only if implementation is approved.

---

# Independent Review

Once your proposal is complete:

Perform a completely fresh Architecture Review.

Treat the proposal as though written by another engineer.

Challenge every assumption.

Attempt to disprove your own recommendation.

Only then produce the final recommendation.

---

# Required Deliverables

Produce:

* TD-023 Resolution Report
* Architecture Review
* ADR (if required)
* Migration Plan
* Risk Assessment
* Testing Strategy
* Backward Compatibility Assessment
* Recommendation

---

# Implementation Gate

Do **not** implement.

Await explicit approval.

---

# Stage 2

Stage 2 remains frozen.

No Job Intelligence implementation begins until:

* TD-023 is resolved
* Stage 1 is formally accepted
* Stage 1 is tagged
* Engineering Release Package is complete

---

# Repository Governance

Continue storing every directive inside:

```
prompts/
```

Maintain the permanent governance directory:

```
orion-governance/
```

These repositories—not AI conversation history—are now the authoritative engineering record.

---

## Additional Chief Architect Note (governance enhancement recommendation)

Since the project is becoming increasingly formalized, create a dedicated directory alongside `orion-governance`:

```text
/orion-directives
    Chief_Architect_Directive_Sprint1.md
    Chief_Architect_Directive_Sprint1_5.md
    Chief_Architect_Directive_Sprint1_6.md
    Chief_Architect_Directive_Sprint2.md
    Chief_Architect_Directive_Sprint3.md
    Chief_Architect_Directive_Sprint3_Stage1.md
    ...
```

Keeping directives separate from general prompts creates a clear distinction between:

* **Engineering governance** (`orion-governance`)
* **Chief Architect directives** (`orion-directives`)
* **Reusable AI prompts** (`prompts`)

As the project grows, that separation will make the repository easier to audit and navigate.
