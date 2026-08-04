# Sprint Approval Process

## Roles
- **Chief Architect** -- reviews sprint deliverables against the
  Engineering Constitution and Architecture Principles, and formally
  authorizes the next sprint.
- **Chief Software Engineer** (Claude, acting in this role) -- plans and
  executes the authorized sprint, produces the deliverables and
  acceptance report, and requests authorization for the next sprint. Does
  not self-authorize scope expansion.

## Sequence
1. A sprint's scope is defined (either as part of the original Master
   Engineering Prompt, e.g. Sprint 1, or as a Chief Architect directive,
   e.g. Sprint 1 Closure).
2. The Chief Software Engineer implements only what is in scope. Anything
   discovered along the way that seems valuable but is out of scope is
   recorded in `docs/TechnicalDebt.md` or a Sprint N+1 implementation
   plan, not implemented ahead of authorization.
3. The Chief Software Engineer produces, at minimum: working
   code/config/docs for everything in scope, a verification record (tests
   actually run, not merely described), and a written acceptance
   report against the sprint's stated success criteria.
4. The Chief Architect reviews the acceptance report and either:
   - Authorizes the next sprint, or
   - Issues a closure/remediation directive (as happened after Sprint 1),
     which itself becomes the next sprint's scope.
5. Implementation of the next sprint's business logic does not begin
   until step 4 produces explicit authorization. A sprint that only plans
   the next sprint (see `docs/SPRINT-2-IMPLEMENTATION-PLAN.md`) is
   compliant even without that authorization, because planning is not
   implementation.

## What forces a new sprint rather than a routine change
Any of: new business/domain logic, a new external integration, a new
product, or a change to the Engineering Constitution itself. Bug fixes,
documentation updates, and safe refactors identified during a repository
review do not require new sprint authorization -- see
`ARCHITECTURE_REVIEW_PROCESS.md` for the line between "safe improvement"
and "requires authorization."
