# Performance Review Checklist

Distilled from Sprint 1.6 Phase 3, which found two real dialect-specific
defects (a partial-index conflict-detection gap and a missing
`PRAGMA foreign_keys` setting) that a purely static review would have
missed.

- [ ] **Indexes** -- every foreign key used in a dominant read pattern is
      indexed (FK creation implies an index in most dialects, but verify
      for the specific database).
- [ ] **Pagination** -- every list endpoint has bounded page size; no
      unbounded `SELECT *` surface reachable by a client.
- [ ] **N+1 queries** -- check relationship loading strategy
      (`lazy="joined"` vs. default lazy) against actual list-endpoint
      usage, not just model definitions.
- [ ] **Migration quality** -- every migration's `downgrade()` actually
      runs; verify with a real upgrade-downgrade-upgrade round-trip
      against the production database engine, not just SQLite.
- [ ] **Dialect portability** -- if tests run against SQLite but
      production is PostgreSQL (or vice versa), explicitly verify every
      partial index, cascade rule, and driver-error-message assumption
      against BOTH. Do not assume dev-database behavior generalizes.
- [ ] **Transaction boundaries** -- multi-step mutations (e.g. cascading
      recomputation after a delete) happen inside one transaction, not
      split across several with a window for partial failure.
- [ ] **Coverage measurement itself** -- confirm the coverage tool is
      correctly configured for the runtime in use (e.g. `concurrency =
      greenlet` for SQLAlchemy async -- see TD-R11). A clean coverage
      number from a misconfigured tool is worse than no number, since it
      creates false confidence.
