# Architecture Review Process

## When an ADR is required
An ADR is required whenever a change: introduces a new technology or
replaces one already chosen (ADR 0001); changes the boundary between
platform and product code (ADR 0002); changes the data model in a way
that affects more than one table's relationships; or changes a security
posture (auth mechanism, secret handling, CORS policy). It is not
required for: adding a new endpoint that follows existing patterns,
adding a test, fixing a bug, or writing documentation.

## Review steps
1. **Identify the problem** precisely enough that a reader unfamiliar
   with the immediate context understands why the status quo is
   insufficient.
2. **Enumerate real options**, including "do nothing" where relevant.
   At least one rejected option must be a plausible one, not a strawman.
3. **State the decision** and the concrete shape it takes (file
   layout, package boundaries, interfaces).
4. **State consequences honestly**, including new risks, new technical
   debt, and anything that becomes harder as a result. An ADR with no
   listed downside has not been reviewed carefully enough.
5. **Verify before claiming done.** If the ADR asserts behavior (e.g.
   "the test suite still passes"), that assertion must correspond to an
   actual run recorded somewhere (acceptance report, CI log), not an
   inference from reading the code.
6. **Update `governance/ADR_INDEX.md`** in the same change.

## Repository review vs. architecture review
A repository review (see `docs/TechnicalDebt.md` and the Sprint 1 Closure
repository review) identifies *symptoms* (duplicate code, weak naming,
layer violations). Not every symptom requires an ADR -- only fix it
directly if the fix is safe and local (rename a variable, delete a
provably-dead file); write it up in `docs/TechnicalDebt.md` if the fix is
correct but risky or large; write an ADR only if the fix changes an
architectural boundary.
