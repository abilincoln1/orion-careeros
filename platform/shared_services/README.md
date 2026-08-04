# Shared Services (Reserved -- Not Yet Implemented)

This directory reserves the location for the ORION Platform's
cross-cutting *services* -- as opposed to `platform/kernel`, which is
importable library code. None of these exist yet; each is documented in
`docs/platform/PLATFORM_KERNEL.md` as a Platform Kernel responsibility and
will be implemented as its own service (or clearly-scoped module) only
when a sprint explicitly authorizes it:

- Notifications
- Event Bus
- Scheduling
- Audit
- Monitoring (beyond the health/readiness endpoints `orion_kernel.health`
  already provides)
- File Storage
- Document Engine
- Communication Hub

Do not add business logic here speculatively. This README exists so the
architecture is legible before the code is; implementation follows
authorization, per the Engineering Constitution's scope discipline.
