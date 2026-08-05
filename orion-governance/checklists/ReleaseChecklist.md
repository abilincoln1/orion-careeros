# Release Checklist

- [ ] Engineering Release Package complete (see
      `EngineeringReleasePackageStandard.md`)
- [ ] All conditions from the preceding review/ARB recommendation closed
      and individually re-verified (not assumed carried over)
- [ ] Verification re-run against the target production environment if
      any fix was made in a different environment (e.g. a sandbox without
      the production database) -- see Sprint 1.6 Condition 5 for the
      reference example
- [ ] Working tree clean -- no stray diagnostic files, no accidentally
      committed embedded repositories or nested clones (check `git
      status` and `.gitignore` before tagging)
- [ ] Release manifest written (`ReleaseManifestTemplate.md`)
- [ ] Git tag created, matching the version scheme in use
      (`vX.Y.Z-sprintN`)
- [ ] Tag pushed with `--tags`; push confirmed by the actual ref update
      shown in output (`sha1..sha2  branch -> branch`), not just absence
      of an error -- PowerShell can render normal git/docker stderr
      output as a misleading `NativeCommandError`; always check for the
      real success signal, not just the absence of red text
- [ ] Post-tag cleanup (if any) done as a **separate** commit that does
      not touch the tagged state
