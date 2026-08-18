# ORION Directives

Chief Architect directives, version-controlled, per the Chief Architect's
recommendation (Sprint 3 Stage 1 Completion directive, 2026-08-06).

## Relationship to other governance locations
- `orion-governance/` -- reusable engineering standards, checklists,
  templates. Evolves independently of any single sprint.
- `orion-directives/` (this directory) -- the actual point-in-time
  directives issued by the Chief Architect, one per sprint/stage.
- `prompts/` -- general-purpose reusable AI prompts, not
  sprint-specific directives.

## Open question, flagged rather than silently resolved
The Chief Architect's recommended structure lists a full history:
`Chief_Architect_Directive_Sprint1.md` through `Sprint3_Stage1.md`.
This repository's actual saved-directive history is incomplete relative
to that list -- only the Sprint 3 governance directive
(`prompts/Chief_Architect_Directive_Sprint03.md`) and this stage's
completion directive were saved to files at the time they were issued;
earlier directives (Sprint 1, Sprint 1.5, Sprint 1.6, Sprint 2) exist
only in prior conversation history, not as committed files.

**Reconstructing them now from memory would risk introducing text that
was never actually the original directive** -- a real accuracy risk
this project's Truth First principle weighs against. Recommend the
project owner confirm whether:
(a) reconstructing them from the original conversation transcripts
    (not from an AI's memory of them) is wanted, or
(b) this directory starts fresh from Sprint 3 onward, with earlier
    sprints' governance history remaining in ADRs, compliance reports,
    and sprint reports (which do already exist and do cite the relevant
    directives by name and date) rather than as standalone directive
    files.

Per the same principle, `Chief_Architect_Directive_Sprint3_Stage1_Completion.md`
remains in `prompts/` for now, exactly where its own explicit
instruction placed it, rather than being silently moved here --
avoiding the same reconstruction-accuracy risk for a file whose
correct location was explicitly stated once already.

## Directives issued so far (update, 14 August 2026)
- `prompts/Chief_Architect_Directive_Sprint03.md` -- Sprint 3 governance + Job Intelligence design authorization (includes v1.1 amendment).
- `prompts/Chief_Architect_Directive_Sprint3_Stage1_Completion.md` -- TD-023 resolution authorization.
- `prompts/Chief_Architect_Directive_Job_Discovery.md` -- Priority 1 closure + lean Job Discovery authorization. **Authoritative version** -- no competing copy exists in this directory, per this README's own established convention above.

## Directory formalized as authoritative directive home (update, 16 August 2026)
Per the Chief Architect's explicit governance guidance:
`/orion-governance/` = standards, ADRs, risk, engineering controls.
`/orion-directives/` = authoritative Chief Architect instructions (this directory).
`/prompts/` = reusable/operational AI prompts.

- `orion-directives/ORION-CA-DIRECTIVE-S3-UI-MVP-001.md` -- Lean CareerOS UI MVP, authoritative, implemented and accepted.
- Earlier directives remain in `prompts/` (historical location, not retroactively moved, to avoid rewriting already-referenced paths). New directives of this kind should be placed here going forward.
