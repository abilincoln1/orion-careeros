# Configuration Integrity Standard

## Why this exists
The same root cause behind Sprint 1.5's reconciliation -- code and its
description silently drifting apart -- can recur in any of seven
distinct artefact types. This standard names them explicitly so "is the
repo internally consistent?" is a checklist, not a vague feeling.

## The seven artefacts
1. **Specification** -- the design document describing what should exist
   (e.g. `docs/CAREER_DNA_MODEL_SPEC.md`).
2. **ADRs** -- the record of why specific decisions were made.
3. **Source Code** -- ground truth of what actually exists. In any
   conflict with any other artefact, the code is authoritative for "what
   is," though not necessarily for "what should be."
4. **Tests** -- proof the code does what the spec/ADRs claim, with a real
   coverage number, not an assumed one (see `EngineeringReleasePackage
   Standard.md` on verification discipline).
5. **Documentation** -- README, ARCHITECTURE.md, API.md, and similar,
   describing the system for a human reader.
6. **Governance** -- RiskRegister.md, TechnicalDebt.md, and process
   documents, describing the system's known risks and debts.
7. **Metrics** -- the machine-generated snapshot (`metrics.json`) of
   coverage, complexity, dependency, and endpoint counts.

## The check
Produce a **Configuration Integrity Matrix**: one row per artefact,
stating what it currently claims about the subject under review, and
whether that claim is consistent with the source code. Any
inconsistency found must be resolved one of two ways:
- **Corrected** -- update the drifted artefact to match reality, in the
  same change (see `EngineeringReleasePackageStandard.md`).
- **Explicitly documented as a deliberate, deferred gap** -- with a
  stated reason and a plan for when it will be corrected (e.g. "metrics
  regeneration deferred until ARB disposition is final, to avoid
  documenting code that might still be rejected").

**Silent, unexplained inconsistency is never an acceptable outcome.**
An explicitly-documented gap is fine; an undocumented one is exactly
Sprint 1.5's failure mode recurring.

## Cadence
Run this check:
- At the end of every sprint, as part of the Engineering Release Package.
- Whenever a Candidate Acceptance Review or equivalent audit is
  performed on already-existing code (per Sprint 1.6's model).
- On demand, whenever anyone (human or AI) suspects drift -- suspicion
  alone is sufficient reason to check; do not wait for a scheduled point.
