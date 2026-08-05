# Definition of Done

A unit of work (task, sprint, ADR-driven change) is **done** only when
all of the following are true. This list is intentionally the same
regardless of how small the change looks -- the Sprint 1 Postgres
verification gap existed precisely because "done" was assumed rather
than checked.

1. **Code compiles / type-checks.** Python: no syntax errors
   (`py_compile` or equivalent). TypeScript: `tsc -b` with zero errors.
2. **Tests exist and pass.** New behavior has a test. The full existing
   suite still passes -- not "should still pass," actually run and the
   output recorded.
3. **Migrations are reversible and applied.** Any schema change has an
   Alembic migration with a working `downgrade()`, and has been applied
   (`upgrade head`) against a real database engine matching production
   (PostgreSQL), not only inferred from SQLite-compatible test runs.
4. **Configuration, not hardcoding.** Any new value that could differ by
   environment or product is a setting, per
   `governance/ARCHITECTURE_PRINCIPLES.md` principle 5.
5. **Documentation updated in the same change.** README, ARCHITECTURE.md,
   API.md, or the relevant governance/platform doc -- whichever the
   change affects -- not deferred to "later."
6. **ADR written if required** (see `ARCHITECTURE_REVIEW_PROCESS.md`),
   and `governance/ADR_INDEX.md` updated.
7. **No unauthorized scope.** Nothing was implemented beyond what the
   current sprint's directive authorized; anything tempting-but-out-of-
   scope was written to `docs/TechnicalDebt.md` or a future sprint plan
   instead.
8. **Verification evidence is honest.** Any claim of the form "X passes"
   or "Y was tested" in a report is backed by an actual command run in
   this session (or a clearly labeled gap, e.g. "no Docker daemon
   available; must be run by the user"). Overstating verification is a
   Truth First violation.
