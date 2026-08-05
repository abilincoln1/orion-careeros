# ADR 0006: Document Intelligence Engine as a Platform Kernel Capability

## Status
Accepted

## Problem
Sprint 3 Stage 1 was originally scoped as "CV Intelligence" -- a
CareerOS-specific CV parser. The Chief Architect redirected this: ORION
is a Career Intelligence Platform, and the capability to ingest and
interpret professional documents (CVs now; cover letters, certificates,
degrees, licences, LinkedIn exports, job descriptions, references,
performance reviews, and skills assessments later) is foundational
infrastructure any future ORION product will need, not a CareerOS-only
concern. This ADR records the resulting architecture and, specifically,
why it's placed in the Platform Kernel despite this project's own
established caution against speculative platform engineering.

## Decision
Build a **Document Intelligence Engine** as a genuine Platform Kernel
capability (`platform/kernel/orion_kernel/document_intelligence/`):
document upload/storage integration, format-specific text extraction,
a provider-agnostic `DocumentExtractionProvider` interface, and a
structured intermediate extraction model (`ExtractionResult`). What to
*do* with extracted data remains CareerOS-specific, in
`document_intelligence_service.py`, which is the only code permitted to
call Career DNA's existing write services.

## Why the kernel, not a CareerOS-local capability (the real tension this ADR resolves)
This project has twice now (ADR 0005 Decisions 1 and 2) reasoned that a
capability should live in the Platform Kernel only once at least two
products need it, not speculatively ahead of real reuse --
`ArchitecturePrinciples.md`'s own stated principle. File Storage
(ADR 0005 Decision 1) was kept CareerOS-local for exactly this reason.

**This decision reaches the opposite conclusion, and the difference is
worth stating precisely rather than treated as an exception:** File
Storage's *purpose* is CareerOS-specific (storing CareerOS's CV
uploads); a second product needing storage would need its own storage,
not necessarily the same mechanism. The Document Intelligence Engine's
*purpose*, as stated in the directive itself, is explicitly
cross-product reuse -- "designed so future ORION products can reuse it
without modification" is not a nice-to-have, it's the reason this
capability was redirected away from "CV Intelligence" in the first
place. Put differently: File Storage is infrastructure a product
happens to need; the Document Intelligence Engine is infrastructure
whose entire justification is being shared. Building it CareerOS-local
now and migrating later (File Storage's chosen path) would mean
re-deriving the provider-abstraction and extraction-model design from
scratch for the second product, which is precisely the rework this
directive's closing note says the platform placement is meant to avoid.

**Consequence of this reasoning being product/context-specific:** this
ADR does not establish "AI-adjacent capabilities go in the kernel" as a
general rule. The next capability proposed for kernel placement should
be evaluated on the same terms (is reuse the stated purpose, or a
possible future benefit of something built for one product's need?),
not on the precedent of this ADR alone.

## Options considered
1. **CareerOS-local**, matching File Storage's pattern. Rejected per
   the reasoning above.
2. **Platform Kernel**, chosen.
3. **A new top-level `/shared` location**, distinct from
   `platform/kernel`. Considered and rejected: ADR 0005 Decision 5
   already declined to create a top-level `/shared` for existing
   reserved placeholders, for lack of a driving need at the time; this
   capability now provides exactly that driving need for the *kernel*
   specifically (a capability with genuine present-day, not
   speculative, cross-product design intent) but not evidence for
   moving unrelated placeholders. Placing it in `platform/kernel`
   rather than reopening the `/shared` question keeps this decision
   scoped to what it actually needs to resolve.

## Consequences
- `orion_kernel` gains its first capability beyond configuration/
  logging/security/database/health/middleware -- a real precedent for
  what "kernel-worthy" means going forward, not just infrastructure
  primitives.
- The provider abstraction (`DocumentExtractionProvider`) and the
  Job Intelligence provider abstraction (`JobProviderClient`, ADR-
  adjacent design in `docs/SPRINT-3-ARCHITECTURE.md`) are structurally
  similar but intentionally not unified into one generic "provider"
  interface in this ADR -- they solve different problems (extracting
  structure from a document vs. fetching listings from an external
  service) and forcing a shared abstraction now would be exactly the
  speculative-generalization this project has learned to avoid. If a
  third provider-shaped need appears, that's the point to reconsider
  whether a shared base interface earns its cost.
- `AttributionSource` gains its final, standardized value set
  (`USER_ENTERED`, `AI_EXTRACTED`, `IMPORTED`, `VERIFIED`) --
  implementing ADR 0005 Decision 3's naming precisely, not just its
  intent.
- TD-019 (write-boundary enforcement) now has a concrete implementation
  target: an import-boundary test on
  `document_intelligence_service.py`, specified in
  `docs/SPRINT-3-STAGE1-TEST-STRATEGY.md`.

## Verification
Not yet performed -- this ADR documents a design decision, prior to
implementation, per the directive's explicit "only after these are
reviewed and approved should implementation begin." Verification will
be the Stage 1 test suite specified in
`docs/SPRINT-3-STAGE1-TEST-STRATEGY.md`, run and reported honestly
(pass/fail, real coverage numbers) once code exists.

## Related documents
- `docs/DOCUMENT-INTELLIGENCE-ARCHITECTURE.md` -- full design.
- `docs/diagrams/document-intelligence-sequence.mmd` -- pipeline
  sequence diagram.
- `docs/SPRINT-3-STAGE1-TEST-STRATEGY.md` -- verification plan.
- `docs/adr/0005-sprint3-foundational-decisions.md` -- Decisions 1
  (File Storage) and 3 (AI Attribution), both directly referenced above.
- `docs/SPRINT-3-ARCHITECTURE.md` -- Section 2 (CV Intelligence) and
  Section 9's related items are superseded by this ADR and the
  architecture document above; left unedited there per this project's
  convention of superseding rather than silently rewriting
  already-reviewed documents.
