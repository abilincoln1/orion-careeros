# ORION Platform -- Engineering Constitution

This is the canonical, binding reference for the principles established in
the Master Engineering Prompt (Project ORION, v2.0) and reaffirmed by the
Chief Architect's Sprint 1 Closure directive. Every ADR, code review, and
sprint plan must be able to point to this document to justify a decision.
If a decision cannot be justified against it, it requires an ADR
explaining the deviation (see `ARCHITECTURE_REVIEW_PROCESS.md`).

## The ten principles

1. **Truth First.** Never fabricate experience, certifications,
   employment, achievements, qualifications, or projects. Every
   recommendation and generated document must be traceable to evidence.
2. **Career Knowledge Base is the source of truth.** Never treat CV
   documents as the master record -- CVs are generated outputs.
3. **Recommendation First.** The platform exists to improve career
   decisions; searching is secondary to recommending.
4. **Human Approval.** No product on the ORION Platform may automatically
   apply for jobs, send recruiter emails, submit applications, or reply
   to recruiters. Always generate drafts for approval.
5. **Explainability.** Every recommendation must explain why it was
   selected: score, strengths, weaknesses, missing skills, salary
   reasoning, commute reasoning. No opaque AI scoring.
6. **Configuration.** Nothing important is hardcoded: salary bands,
   commute radius, contract weighting, remote preference, match
   thresholds, company watchlists, and learning priorities must all be
   configurable.
7. **Docker First.** The entire system must run locally on the primary
   development platform (Windows + Docker Compose), with no cloud
   dependency.
8. **API First.** Every capability is exposed through a documented REST
   API; frontends consume backend APIs, never internals directly.
9. **Test First.** Every sprint includes unit tests, API tests, migration
   validation, and Docker verification.
10. **ADR Governance.** Any architectural change outside the approved
    specification requires an Architecture Decision Record documenting
    the problem, options considered, decision, and consequences.

## Platform vs. product scope discipline

Introduced at Sprint 1 Closure: ORION is the platform; CareerOS is a
product built on it. Platform Kernel capabilities (see
`docs/platform/PLATFORM_KERNEL.md`) are implemented once and consumed by
every product. Product-specific business logic, AI functionality, and
domain features belong in `/products/<product>`, never in `/platform`.

## Authority

This document is maintained under `/governance` and referenced by
`ARCHITECTURE_PRINCIPLES.md`, `QUALITY_GATES.md`, and
`DEFINITION_OF_DONE.md`. Amending it is itself an architectural decision
and requires an ADR (see `ADR_INDEX.md`).
