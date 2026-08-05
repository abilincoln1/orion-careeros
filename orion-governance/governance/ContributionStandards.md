# Contribution Standards

These apply to any change to the repository, whether made by the Chief
Software Engineer (Claude) or a future human/automated contributor.

## Before starting
- Read the relevant governance docs for the area you're touching
  (`ARCHITECTURE_PRINCIPLES.md` for structure, `CODING_STANDARDS.md` for
  style, `PLATFORM_KERNEL.md` if touching `/platform`).
- Check `docs/TechnicalDebt.md` and `docs/RiskRegister.md` -- you may be
  about to fix something already tracked, or about to reintroduce
  something already flagged as risky.

## While working
- Prefer the smallest change that correctly solves the stated problem.
  Do not use an authorized task as license to also refactor unrelated
  code, rename unrelated things, or add unrequested functionality (see
  `SPRINT_APPROVAL_PROCESS.md` on scope discipline).
- Any new configuration value goes into the appropriate `Settings` class
  (platform-level in `OrionBaseSettings` only if every product needs it;
  otherwise product-level), never as a literal.
- Any change to `/platform/kernel` must be justified by more than one
  product's need, or by CareerOS's demonstrated current need -- see ADR
  0002's rationale for why premature sharing was rejected.

## Before calling it done
- Run the tests. Not "the tests should pass" -- run them, read the
  output, and only then say they pass.
- Update the docs that describe what you changed.
- Check whether your change created new technical debt or risk worth
  recording, even if the change itself is complete and correct.

## Commit/change hygiene (for when this repository is placed under git)
- One logical change per commit; a repository restructure and a bug fix
  are two commits, not one.
- Commit messages describe *why*, not just *what* ("extract shared config
  base so a second product can reuse it" not "move files").
