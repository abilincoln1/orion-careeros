# Sprint Documentation

Per the Claude Cowork Engineering Constitution, every sprint produces
sprint documentation. This directory is the canonical home for that
documentation **going forward, starting Sprint 2**.

## Existing sprint documentation (Sprint 1)

Sprint 1 and Sprint 1 Closure's sprint documents were written before this
directory existed and live at the top level of `docs/` instead:

- `docs/SPRINT-1-REVIEW.md`
- `docs/SPRINT-1-ACCEPTANCE-REPORT.md`
- `docs/SPRINT-2-ARCHITECTURE-REVIEW.md`
- `docs/SPRINT-2-IMPLEMENTATION-PLAN.md`
- `docs/SPRINT-2-READINESS-REPORT.md`
- `docs/Sprint1_Closure_Compliance_Report.docx`
- `docs/CareerOS_Sprint1_Compliance_Report.docx`

They were **not moved** here during the Project Baseline pass (2026-08-05)
because at least 32 cross-references to their current paths exist across
`README.md`, `orion-governance/`, and other `docs/` files. Moving them would
have required rewriting every cross-reference as a side effect of a
baseline/hygiene task, which risked silently breaking documentation
integrity. This is a deliberate, documented deviation from the letter of
the constitution's directory convention — see `docs/PROJECT_BASELINE.md`
for the full rationale.

**Convention from Sprint 2 onward:** new sprint plans, reviews, and
acceptance reports go in `docs/sprints/`, named
`SPRINT-<n>-<PLAN|REVIEW|ACCEPTANCE-REPORT>.md`.
