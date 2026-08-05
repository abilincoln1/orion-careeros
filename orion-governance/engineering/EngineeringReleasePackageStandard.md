# Engineering Release Package Standard

## Why this exists
Sprint 1.5's Repository Reconciliation Report found the repository's
governance documentation and its actual code had silently diverged --
Career DNA was fully implemented while multiple committed reports
insisted it wasn't. The root cause was that "the sprint is done" and
"the paperwork agrees with the code" were treated as separable events.
This standard makes them the same event.

## The rule
**No sprint is considered accepted until its Engineering Release
Package exists, in the same change that accepts it.** Not before
(don't document code that might still be rejected) and not
indefinitely after (a promise to update docs "later" is exactly the
failure mode that caused Sprint 1.5).

## Required contents
1. **Accepted source code** -- the actual diff, or a pointer to it.
2. **Updated documentation** -- README, ARCHITECTURE.md, API.md, and any
   other doc whose claims the sprint's work affects. Verify by grep, not
   memory: search the docs for language the sprint made false.
3. **Updated architecture diagrams**, if the sprint changed structure.
4. **Updated metrics** -- regenerated via the project's actual metrics
   tooling (`scripts/metrics/collect_metrics.py` or its successor), never
   hand-computed. See `ConfigurationIntegrityStandard.md`.
5. **Updated ADR index** -- every architectural decision made or
   confirmed during the sprint has a corresponding ADR, indexed.
6. **Updated governance records** -- `RiskRegister.md` and
   `TechnicalDebt.md`, including closing out (not silently leaving open)
   any item the sprint resolved, filed under the correct convention
   (see `TechnicalDebtStandard.md`).
7. **Git tag** -- e.g. `v0.2.0-sprint2`, created only after every item
   above is verified, never before.
8. **A release manifest** -- a short, human-readable summary of exactly
   what changed, in the shape of `orion-governance/templates/
   ReleaseManifestTemplate.md`.

## What "prepared but not published" means
When a directive asks for a package to be "prepared, not published"
(e.g. Sprint 1.6's Phase 9), every item above except the git tag should
exist and be reviewable. The tag is the explicit publication step and
requires separate authorization -- see `SprintApprovalProcess.md`.

## Verification discipline
Every claim in the release package ("tests pass," "coverage is X%," "no
broken links") must be backed by a command actually run in the session
that produced the package, per `DefinitionOfDone.md` principle 8. If
something couldn't be verified in the current environment (e.g. no
Postgres available), say so plainly and name what verification is still
outstanding -- do not claim it as done. Sprint 1.6's Condition 5
(Postgres round-trip re-verification, deferred to the human operator's
machine, then actually confirmed before the tag was created) is the
reference example of doing this correctly.
