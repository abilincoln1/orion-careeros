# PROJECT ORION

## CHIEF ARCHITECT DIRECTIVE

### Sprint 3 -- ORION Governance Foundation & Job Intelligence Platform

### Version 1.0 (Authorised)

**To:** Claude Cowork Engineering Team
**From:** Chief Solutions Architect (ChatGPT)
**Project:** ORION Platform
**Date:** 05 August 2026

---

# Executive Directive

The ORION Architecture Review Board has formally accepted:

* Sprint 1
* Sprint 1 Closure
* Sprint 1.5 Repository Reconciliation
* Sprint 1.6 Candidate Acceptance Review

The Career DNA implementation has now been accepted as:

**Sprint 2 -- Accepted (v0.2.0-sprint2)**

The repository is now considered the authoritative baseline.

From this point onward:

* The repository is the source of truth.
* Previous chat history must not be relied upon.
* All architectural decisions must be traceable through ADRs, governance records, Git history, and Engineering Release Packages.

Before implementing Sprint 3 functionality, the ORION Platform itself must be strengthened.

---

# Primary Objectives

This sprint has two equally important goals:

1. Build a permanent ORION Governance Framework.
2. Design and begin implementation of the CareerOS Job Intelligence Platform.

---

# Phase 0 -- Repository Assessment

Before making any changes:

Read and understand the repository.

Review:

* README.md
* docs/
* platform/
* products/
* governance/
* ADRs
* Technical Debt Register
* Risk Register
* Engineering Release Package
* Metrics
* Sprint reports

Produce a concise Project State Assessment.

Do not assume previous chat history.

Treat the repository as authoritative.

---

# Phase 1 -- Create Permanent ORION Governance Framework

Create a permanent platform-level directory:

```text
/orion-governance
```

This directory belongs to ORION itself--not CareerOS.

Its purpose is to provide reusable engineering governance for every future ORION product.

CareerOS becomes the first consumer.

Future products must inherit these standards.

---

## Required Structure

```text
/orion-governance

    /architecture
        ADR_TEMPLATE.md
        ADR_INDEX.md
        ArchitectureReviewChecklist.md

    /engineering
        EngineeringReleasePackageStandard.md
        ConfigurationIntegrityStandard.md
        DefinitionOfDone.md
        QualityGates.md

    /governance
        SprintApprovalProcess.md
        RepositoryStandards.md
        CodingStandards.md
        ContributionStandards.md

    /risk
        RiskManagementStandard.md
        TechnicalDebtStandard.md

    /templates
        SprintTemplate.md
        ComplianceReportTemplate.md
        ReleaseManifestTemplate.md
        ArchitectureReviewTemplate.md

    /checklists
        SprintClosureChecklist.md
        SecurityReviewChecklist.md
        PerformanceReviewChecklist.md
        ReleaseChecklist.md

README.md
```

---

# Phase 2 -- Governance Migration

Review the existing governance documents.

Move reusable governance documents into the ORION Governance Framework.

Leave product-specific documentation within CareerOS.

Update all links and references.

No broken documentation links are acceptable.

---

# Phase 3 -- Update Repository Architecture

The target repository structure becomes:

```text
ORION

platform/
    kernel/

orion-governance/

shared/

products/
    careeros/
```

Maintain strict separation:

Platform

down arrow

Governance

down arrow

Shared Components

down arrow

Products

No product may own platform governance.

---

# Phase 4 -- Configuration Integrity

Update the Configuration Integrity Matrix.

Verify consistency between:

* Specifications
* ADRs
* Source Code
* Tests
* Documentation
* Governance
* Metrics
* Engineering Release Package

Any inconsistency must either be corrected or explicitly documented.

---

# Phase 5 -- Sprint 3 Architecture

Design the Job Intelligence Platform.

Do not immediately build features.

First produce the architecture.

---

## Required Components

### Career DNA

Use the accepted Sprint 2 implementation.

No redesign without approval.

---

### CV Intelligence

Design a service capable of:

* CV parsing
* Skill extraction
* Technology extraction
* Employment extraction
* Education extraction
* Certification extraction

Produce structured Career DNA.

---

### Job Intelligence

Design a provider-based architecture.

Potential providers include:

* JobServe
* Indeed
* Reed
* CV-Library
* TotalJobs

Use official APIs where available, RSS feeds where permitted, or user-authorised/manual imports. Do **not** implement scraping or automation that violates any provider's terms of service.

All providers must implement a common interface.

---

### Matching Engine

Design scoring for:

* Skills
* Technologies
* Employment history
* Industry
* Salary
* Location
* Work preference

Produce a transparent matching model that explains why a match scored highly or poorly.

---

### Recruiter Watchlist

Design a recruiter relationship management module.

Track:

* Recruiters
* Agencies
* Companies
* Contact history
* Notes
* Follow-ups
* Response history

This is a user-managed CRM. Do not automate outreach.

---

### Interview Pipeline

Design workflow:

Applied

down arrow

Recruiter Contact

down arrow

Interview 1

down arrow

Interview 2

down arrow

Technical

down arrow

Offer

down arrow

Accepted / Rejected

Provide dashboards and reporting.

---

# Phase 6 -- Architecture Review

Produce:

* System Architecture
* Module Diagram
* Domain Model
* Database Design
* Service Boundaries
* Provider Interface Specification

No implementation before review.

---

# Phase 7 -- Engineering Standards

Every Sprint 3 component must satisfy ORION standards:

* Unit tests
* Integration tests
* API tests
* Documentation
* ADRs (where applicable)
* Metrics updates
* Risk review
* Technical debt review
* Engineering Release Package

No component is complete until these artefacts exist.

---

# Deliverables

Produce:

1. Project State Assessment
2. ORION Governance Framework
3. Governance Migration Report
4. Updated Repository Architecture
5. Configuration Integrity Report
6. Sprint 3 Architecture Review
7. Job Intelligence Architecture
8. Provider Interface Specification
9. Matching Engine Design
10. Recruiter Watchlist Design
11. Interview Pipeline Design
12. Sprint 3 Implementation Plan
13. Updated Technical Debt Register
14. Updated Risk Register

---

# Working Principles

* Repository is the single source of truth.
* Do not rely on previous chat history.
* Do not implement functionality outside the approved sprint scope.
* Record every architectural decision through ADRs.
* Update documentation and governance as changes are made.
* Produce evidence for every significant engineering claim.
* Raise uncertainties instead of making assumptions.

---

# Success Criteria

Sprint 3 Foundation is successful when:

* ORION has a reusable governance framework independent of CareerOS.
* Repository architecture cleanly separates platform, governance, shared components, and products.
* Configuration Integrity is maintained.
* The Job Intelligence Platform architecture is complete and approved.
* CareerOS is ready for Sprint 3 implementation with a stable, governed foundation.

**Do not begin Sprint 3 feature implementation until the architecture, governance migration, and design deliverables have been completed and approved.**

---

# AMENDMENT -- Version 1.1 (Final)

**Re:** Sprint 3 -- Phase 6 Approval & Implementation Authorisation
**Date:** 05 August 2026

*Filed as an amendment to this same directive, not a separate file,*
*since it is explicitly versioned "v1.1" of the Sprint 3 lineage above,*
*not a new sprint number. See `docs/SPRINT-3-PROJECT-STATE-ASSESSMENT.md`*
*and `docs/SPRINT-3-ARCHITECTURE-REVIEW.md` for the work this amendment*
*authorized and reviewed.*

## Executive Decision

The Sprint 3 Phase 0-6 Closure Report has been reviewed.

The Architecture Review Board concludes that the governance work has been completed to a high standard and that the repository has reached an appropriate level of maturity.

The establishment of `/orion-governance` is approved as a permanent part of the ORION Platform architecture.

This directory shall remain the canonical location for reusable governance, standards, templates, checklists, ADRs, and engineering processes for all present and future ORION products.

CareerOS is designated as the first consumer of the ORION Governance Framework.

## Phase 6 Independent Architecture Review

Authorisation is granted to perform an independent Phase 6 Architecture Review.

The review must be conducted as if evaluating a third-party pull request. Do not defend previous implementation choices. Challenge assumptions. Attempt to identify architectural weaknesses.

Evaluate: Domain boundaries, Service boundaries, Provider abstraction, Database design, Kernel responsibilities, Product responsibilities, Future extensibility, Maintainability, Testability, AI-readiness.

Produce one recommendation: Approve / Approve with Conditions / Reject. Support every recommendation with evidence. No implementation work is to begin until this review is complete.

## Architectural Decisions

### Decision 1 -- File Storage
Implement a CareerOS-local File Storage Adapter. Do not build a Platform Kernel File Storage capability at this stage. ORION currently has only one production consumer; a platform service should not be created until at least two products demonstrate the same requirement. Design the storage layer behind an interface so migration to a shared Platform File Storage service can occur later without changing business logic.

### Decision 2 -- Job Provider Scheduling
Implement scheduling as a reusable Platform capability. Recurring ingestion is fundamental infrastructure rather than CareerOS-specific business logic and is likely to be reused by future ORION products. Design it as a scheduler service with provider-independent interfaces.

### Decision 3 -- AI Attribution
Introduce a new attribution source. Current values should distinguish between: user entered; AI extracted from user documents; imported from external systems; verified manually. Do not classify AI-extracted information as self-reported. The provenance of information is part of the product's trust model, and future AI reasoning depends upon accurate provenance.

### Decision 4 -- Job Listing Lifecycle
Adopt soft deletion. Inactive listings shall be marked expired. Never destroy historical records referenced by match results, applications, recruiter interactions, or analytics. Historical integrity is more valuable than aggressive cleanup.

### Decision 5 -- `/shared` Repository Structure
Do not perform the restructure during Sprint 3. Close TD-018 as Deferred by Architecture Decision. The current structure is internally consistent and the proposed change offers little functional benefit; repository stability is preferable to cosmetic restructuring. Revisit only if a second ORION product requires broader shared libraries.

## Sprint 3 Implementation Authorisation

Upon successful completion of the independent Phase 6 review, implementation of Sprint 3 is authorised, proceeding incrementally: Stage 1 CV Intelligence, Stage 2 Job Provider Framework, Stage 3 Matching Engine, Stage 4 Recruiter Watchlist, Stage 5 Interview Pipeline. No stage may begin until the previous stage satisfies the ORION Definition of Done.

## Permanent Engineering Standard

`/orion-governance` is now part of the permanent ORION architecture, containing reusable engineering governance for every ORION product, evolving independently of any individual product. Products inherit governance from ORION; they do not own it.

## Sprint Directives

Effective immediately, every Chief Architect directive shall be version-controlled and stored within `/prompts/`, named `Chief_Architect_Directive_SprintNN.md`, becoming part of the permanent engineering record.

## Deliverables (this amendment)

1. Independent Phase 6 Architecture Review Report.
2. Updated Technical Debt Register reflecting the architecture decisions above.
3. Updated Risk Register where required.
4. ADR documenting the five architecture decisions.
5. Confirmation that `/orion-governance` is fully integrated into the repository.
6. Save this directive as `prompts/Chief_Architect_Directive_Sprint03.md`.

## Final Authorisation

Once the Independent Phase 6 Architecture Review has been completed and the deliverables above have been accepted, Sprint 3 implementation is authorised. The first implementation work shall be CV Intelligence, using the accepted Sprint 2 Career DNA model as the sole write path, preserving all existing domain invariants and maintaining full compliance with the ORION Governance Framework.
