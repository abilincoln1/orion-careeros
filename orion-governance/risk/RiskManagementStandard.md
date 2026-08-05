# Risk Management Standard

## Categories in use
Distilled from `docs/RiskRegister.md`'s existing, proven structure --
not invented fresh:
- **Technical risks (RT-)** -- engineering/infrastructure risk (e.g.
  unverified deployment paths, single-consumer APIs).
- **Security risks (RS-)** -- vulnerabilities, missing controls.
- **Operational risks (RO-)** -- process/people risk (single-reviewer
  projects, missing backups, missing monitoring).
- **Business risks (RB-)** -- risk to the product's credibility or
  mission, including governance discipline itself (RB-01, the scope-creep
  risk that materialized and triggered Sprint 1.5, is the canonical
  example of why this category matters as much as technical risk).
- **Platform risks (RP-)** -- risk specific to the platform/product
  boundary (kernel misuse, premature shared-code speculation).

## Fields every entry needs
ID, Risk (one sentence), Likelihood (Low/Medium/High), Impact
(Low/Medium/High), Mitigation (specific action, not "will monitor"),
Owner (a role, not necessarily a named individual on a
single-contributor project), Status (Open / Mitigated / Accepted /
Closed).

## A rule this project learned the hard way
**A risk marked "Mitigated" must cite the specific action that
mitigated it, and that action must be true.** RB-01 was marked
Mitigated on the claim "this work deliberately implements none [Career
DNA]" -- false as of the same commit. A mitigation claim is a factual
assertion subject to the same Truth First discipline as any other
engineering claim (`DefinitionOfDone.md` principle 8). If a risk
materializes, correct the entry to say so and describe what actually
resolved it -- do not leave a false "Mitigated" standing.

## Re-review trigger
Any Configuration Integrity check (see `ConfigurationIntegrityStandard.md`)
that finds implemented code contradicting a risk register entry must
re-open that entry for review as part of the same pass, not defer it.
