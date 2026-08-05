# ADR NNNN: <Short, specific title>

## Status
<Proposed | Accepted | Accepted (retroactively documented) | Superseded by NNNN | Deferred>

## Problem
What forced this decision? State the constraint or requirement plainly,
not the solution. If this ADR is retroactive (written after the code
already existed), say so explicitly and name the source that shows the
decision was genuinely deliberate at implementation time (a spec, a
review report, a test) -- do not invent reasoning after the fact.

## Options considered
List every option seriously considered, including the one rejected.
"We didn't consider alternatives" is a signal the decision needs more
thought, not a valid ADR.

## Decision
State the chosen option in one sentence, then justify it against the
rejected alternatives specifically -- not against a strawman.

## Consequences
- What does this make easier?
- What does this make harder, or what debt does it create? If it creates
  technical debt, it must also get a corresponding entry in
  `/orion-governance/risk/TechnicalDebtStandard.md`'s register -- an ADR
  documenting a trade-off does not substitute for tracking its cost.
- What does this foreclose or keep open for later?

## Verification
How was this decision's correctness actually checked, not just argued
for? A test, a reproduction script, a load test, a security scan --
name the specific evidence. Per `/orion-governance/engineering/
DefinitionOfDone.md` principle 8 (Truth First), a claim in this section
must be backed by something actually run, not inferred from reading code.

## Related documents
Link the spec, prior ADRs, review reports, or tests this decision
depends on or is verified by.
