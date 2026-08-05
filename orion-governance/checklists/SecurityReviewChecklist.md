# Security Review Checklist

Distilled from Sprint 1.6 Phase 2, which found and fixed a real High
severity issue using exactly this structure.

- [ ] **Ownership scoping** -- every mutating/reading endpoint resolves
      the acting identity from the authenticated token, never from a
      client-supplied id. Verify with a real cross-user test, not by
      reading the code.
- [ ] **Input validation** -- schema-level constraints exist for every
      field with a real bound (length, range, enum). Custom validators
      are tested for their rejection path, not just their acceptance path.
- [ ] **Injection** -- no raw SQL string interpolation; ORM/parameterized
      queries throughout.
- [ ] **Error handling** -- trigger each custom exception handler with a
      real request that hits it (not just imagine it works). Sprint 1.6
      found a validation-handler crash this way that static reading
      missed entirely.
- [ ] **Dependency CVEs** -- run the project's actual audit tool
      (`pip-audit`/`npm audit` or equivalent); do not assume "no new
      dependencies" means "no new findings," since transitive
      dependencies shift.
- [ ] **Secret handling** -- no secrets in code or committed config;
      placeholder values in `.env.example` are clearly marked insecure.
- [ ] **Audit logging** -- for any new mutation surface, confirm whether
      audit logging is in scope for this sprint or explicitly deferred
      (don't leave it unaddressed silently).

## Severity classification
Critical / High / Medium / Low / Informational. A review with zero
findings at any severity for a genuinely new surface is itself
suspicious -- reconsider whether the review was thorough enough before
reporting a clean result.
