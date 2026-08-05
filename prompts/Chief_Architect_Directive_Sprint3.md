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
