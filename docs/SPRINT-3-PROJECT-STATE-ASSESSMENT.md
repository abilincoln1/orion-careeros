# Sprint 3 -- Project State Assessment (Phase 0)

Produced from a fresh clone of the repository at commit `d82bbf6`
(tag `v0.2.0-sprint2`), per the directive's instruction to treat the
repository, not prior conversation, as authoritative.

## Confirmed state at sprint start
- **Tag `v0.2.0-sprint2` present**, marking Career DNA's formal
  acceptance: 24 entities, 2 migrations, 21 endpoints, 4 services.
- **Test coverage: 96.01%** overall (measured with `.coveragerc`'s
  `concurrency = greenlet` setting -- required for accurate SQLAlchemy
  async coverage; its absence was itself a defect found and fixed in
  Sprint 1.6, see TD-R11).
- **Technical debt: 13 open, 11 resolved**, correctly filed under the
  `TD-`/`TD-R` numbering convention `scripts/metrics/collect_metrics.py`
  depends on.
- **Governance**: `RiskRegister.md` RB-01 correctly reflects the
  scope-creep risk that materialized and was subsequently resolved (not
  left on its original false "Mitigated" claim). ADR 0004 documents the
  Career DNA architecture retroactively but accurately.
- **Working tree clean** -- the embedded-repository/stray-file cleanup
  from the prior session (commit `d82bbf6`) is confirmed present.

## What this sprint changed
Per the directive, this sprint's own scope is governance restructuring
and Sprint 3 design -- explicitly not feature implementation. Confirmed
via `git diff --stat` against `d82bbf6`: every changed or new file is
under `docs/`, `orion-governance/`, `README.md`, or a documentation-only
reference fix in 2 files (one `.md`, one `.py` docstring/comment). No
file under `products/` (excluding the doc-reference fix) or
`platform/kernel` was modified in a way that changes behavior.

## Assumptions made, flagged rather than silently applied
1. The directive's target `/shared` top-level directory was **not**
   created by moving `platform/shared_*` there -- filed as TD-018,
   pending your confirmation. See
   `docs/SPRINT-3-CONFIGURATION-INTEGRITY-REPORT.md`.
2. Historical, point-in-time reports referencing the old `governance/`
   path were left with their original text unedited, consistent with
   this project's established convention (ADR 0002's amendment note,
   Sprint 1.6's supersession banners) -- not treated as "broken links"
   requiring correction.
3. Sprint 3's new design documents (`SPRINT-3-ARCHITECTURE.md` and
   related) were placed in `docs/`, alongside Career DNA's own spec
   (`CAREER_DNA_MODEL_SPEC.md`), following this repository's existing
   convention of product-specific specs living at `docs/` root rather
   than under `products/careeros/docs/`.

## Readiness for Sprint 3 implementation
**Not yet ready.** Four open questions in `docs/SPRINT-3-ARCHITECTURE.md`
Section 7 require Chief Architect input (file storage, scheduling,
CV-extraction attribution semantics, job-listing lifecycle), and Phase 6
(independent architecture review) has not yet been performed against
this design -- both are explicit prerequisites per the directive before
any implementation may begin.
