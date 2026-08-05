# Technical Debt Standard

## The convention already in use
`docs/TechnicalDebt.md` uses two tables and a mechanical numbering rule
that `scripts/metrics/collect_metrics.py` parses automatically via
regex: open items are `TD-\d+`, resolved items are `TD-R\d+`. **This
numbering is load-bearing, not cosmetic** -- the metrics pipeline's
"technical debt: N open, M resolved" figure is derived directly from
counting rows matching each pattern.

## The rule this project learned the hard way
An item is only "resolved" for metrics purposes if it is **moved to the
`## Resolved` table under a `TD-R` id**. Writing "Resolved this session"
in the Remediation column of a row still under `## Open` with a plain
`TD-` id does not count -- Sprint 1.6 made exactly this mistake and had
to correct it before the metrics regeneration was accurate. Always move
the row, don't just reword it.

## Fields every entry needs
**Open:** ID, Category, Description, Impact, Remediation (the specific
planned fix, not a vague intention), Priority (Low/Medium/High).
**Resolved:** ID, Category, Description, Resolved by (what specific
change fixed it, with enough detail that "was this actually fixed?" is
answerable without re-deriving the fix from scratch).

## When to add an entry
Any time a review (architecture, security, performance, API, or a
Configuration Integrity check) finds something real that is not fixed
in the same session -- a debt entry is the record that it was found and
not silently dropped. Per `DefinitionOfDone.md` principle 7, tempting-
but-out-of-scope work must be written here or to a future sprint plan,
not implemented ahead of authorization and not forgotten either.

## When NOT to add an entry
Don't create a debt entry for something fixed immediately in the same
session -- that goes straight to the `## Resolved` table (or doesn't
need an entry at all if it was trivial and has no ongoing relevance).
Debt entries are for things that remain true after the session ends.
