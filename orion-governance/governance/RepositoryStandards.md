# Repository Standards

## Top-level layout (authoritative)
```
/platform          ORION Platform Kernel + reserved shared-code locations
/products           ORION products (CareerOS is the first)
/governance          This directory: constitution, principles, process
/docs               Architecture, API, ADRs, reports, registers, metrics
/scripts            Developer convenience scripts (dev up, tests, migrations, metrics)
/config             Non-secret domain configuration (example/future shape)
/prompts            Reserved for AI prompt templates (future sprints)
/tests              Reserved for cross-product/integration tests (future)
/data               Reserved for local data artifacts (gitignored)
```
A new top-level directory requires an ADR (it's an architecture change by
definition). A new directory *inside* an existing top-level one (e.g. a
new product under `/products`) does not, provided it follows the existing
pattern.

## Where new code goes
- Reusable across every conceivable ORION product, and actually needed by
  more than a hypothetical: `/platform/kernel`.
- Reusable in principle but not yet needed by a second consumer:
  documented in the relevant `/platform/shared_*` README, not built.
- Specific to one product: `/products/<product>`.

## File hygiene
- No committed build artifacts: `node_modules/`, `.venv/`, `__pycache__/`,
  `.pytest_cache/`, `*.egg-info/`, `dist/` are all gitignored (see
  `.gitignore`) and must never be manually added back.
- `.dockerignore` lives at the repository root because the backend's
  Docker build context is the repository root (see ADR 0002) -- a
  `.dockerignore` inside a subdirectory has no effect on that build and
  must not be reintroduced.
- Every directory that exists but is intentionally empty (a reserved
  location) contains a `README.md` explaining why, so an empty directory
  is never ambiguous between "reserved" and "forgotten."

## Documentation placement
- Process/standards that apply platform-wide: `/governance`.
- Point-in-time reports (sprint reviews, acceptance reports, compliance
  reports): `/docs`.
- Living registers that are updated over time (technical debt, risk):
  `/docs`, referenced from `/governance` and from `DEFINITION_OF_DONE.md`.
