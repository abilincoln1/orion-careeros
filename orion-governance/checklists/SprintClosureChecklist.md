# Sprint Closure Checklist

- [ ] All Engineering Release Package items exist (see
      `EngineeringReleasePackageStandard.md`)
- [ ] Configuration Integrity Matrix produced; every inconsistency
      corrected or explicitly documented (see
      `ConfigurationIntegrityStandard.md`)
- [ ] Test suite passes; coverage regenerated with the correct
      measurement config (check `.coveragerc`/equivalent exists and is
      current -- see TD-R11 for why this matters)
- [ ] Metrics regenerated via the actual tooling, not hand-computed
- [ ] Every new architectural decision has an ADR; ADR index updated
- [ ] RiskRegister.md and TechnicalDebt.md reviewed -- new items added,
      resolved items correctly moved (not just reworded) per
      `TechnicalDebtStandard.md`
- [ ] Historical documents that this sprint contradicts are formally
      superseded (banner + preserved original text), never silently edited
- [ ] If verification required an environment unavailable in this
      session (e.g. a live database), that verification was either
      obtained from the human operator or explicitly listed as
      outstanding -- never assumed
- [ ] Git tag created only after every item above is true
