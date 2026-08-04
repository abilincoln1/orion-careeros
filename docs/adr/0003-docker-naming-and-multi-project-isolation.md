# ADR 0003: Docker Naming, Multi-Project Isolation, and Platform Kernel Distribution

## Status
Accepted (naming/isolation) / Deferred (kernel distribution -- see Decision 2)

## Context
This ADR responds to the Chief Architect's "Docker Build Review & Sprint 2
Readiness" directive, which established a fact about the development
machine that earlier documents did not account for: `C:\Projects` holds
multiple **completely separate, independently-cloned repositories** (e.g.
`Career OS` and `NDIP`), not a single monorepo with multiple products
underneath it. The ORION Platform Kernel currently lives inside the
CareerOS repository only (per ADR 0002); other ORION products are
expected to be their own separate repositories, not siblings under this
repo's `/products` directory.

Two consequences follow from that fact, addressed as two separate
decisions below.

## Decision 1: Docker naming and network isolation
**Problem:** the original `docker-compose.yml` used generic-within-product
names (`careeros_db`, `careeros_backend`, `careeros_frontend`, volume
`careeros_db_data`) and fixed host ports (`5432`, `8000`, `5173`) with no
naming convention tying them to ORION as a platform. If a second ORION
product (or an unrelated project like NDIP) happened to also publish
Postgres on `5432` or a web server on `8000`, running both stacks at once
on the same machine would either fail outright (port already allocated)
or -- worse -- silently succeed against the wrong container if names ever
collided.

**Decision:** every ORION product's Compose project uses the pattern
`orion-<product>-*`:

```
Compose project name:  orion-careeros
Containers:             orion-careeros-db, orion-careeros-backend, orion-careeros-frontend
Images:                 orion-careeros-backend, orion-careeros-frontend
Network:                orion-careeros-network
Volume:                 orion-careeros-db-data
```

Host-side ports are now overridable via `.env` (`POSTGRES_PORT`,
`BACKEND_PORT`, `FRONTEND_PORT`; container-internal ports are unchanged)
so a developer who hits a real collision with another project can resolve
it with a one-line `.env` edit instead of hand-editing
`docker-compose.yml`. Defaults are unchanged (`5432`/`8000`/`5173`) so
existing bookmarks/muscle memory keep working when there's no collision.

A future ORION product's own repository (NDIP or otherwise) is expected
to follow the same `orion-<product>-*` convention in its own
`docker-compose.yml`, giving every product predictable, collision-resistant
names without the two repositories needing to know anything about each
other.

## Decision 2: Platform Kernel distribution across independent repositories
**Problem:** `products/careeros/backend/requirements.txt` installs the
kernel with `-e ../../../platform/kernel` -- a path relative to
CareerOS's own repository checkout. This works today because the kernel
and its only consumer live in the same repository (ADR 0002). It
**cannot** work for a second product that is a genuinely separate
repository (e.g. NDIP, or a future PropertyOps), because a relative
filesystem path cannot cross from one independent git checkout into
another -- NDIP's own clone would have no `platform/kernel` directory at
all, three levels up or otherwise. Correcting this expectation is the
main reason this ADR exists (see the amendment added to ADR 0002).

**Options considered:**

1. **Do nothing yet; keep the kernel monorepo-only, consumable only by
   products inside this repository.** (chosen for now)
2. Vendor/copy `orion_kernel`'s source into each new product's repo.
3. Add `orion_kernel` to each new product's repo as a git submodule.
4. Publish `orion_kernel` as a normal installable package -- either to a
   private package index, or (lower-friction) installed directly via pip's
   git support, e.g. `pip install git+https://.../orion-kernel.git@v0.1.0`,
   with each product pinning its own compatible version.

Option 2 was rejected outright: it's exactly the code duplication the
Platform Kernel exists to prevent (ADR 0002), and it would silently
diverge over time. Option 3 (submodules) was rejected as unnecessary
operational complexity for a single-kernel, single-team setup -- it adds
a second thing every developer has to remember to `git submodule update`,
for a benefit (in-tree source visibility) the kernel doesn't currently
need. Option 4 is the right long-term answer once a second product
actually exists and needs the kernel: it requires the kernel to have its
own release/versioning discipline (tags, changelog) so consuming products
can pin a version rather than always tracking a moving `main` branch --
a small but real process cost that isn't worth paying before there's a
second consumer to justify it.

**Decision:** keep Option 1 for Sprint 1 Closure and Sprint 2 (Career DNA
Service is CareerOS-only and doesn't need this). This is an explicit,
documented limitation, not an oversight: **`orion_kernel` cannot currently
be consumed by a product in a separate repository (NDIP or otherwise)
without a packaging change.** Per the directive that created this ADR,
that packaging change (Option 4) is **not implemented now**. When a real
second product needs the kernel, implementing Option 4 should be a small,
self-contained task: add a version tag to this repository (or extract
`platform/kernel` to its own repository at that point, if preferred),
and have the new product's `requirements.txt` reference it via
`git+https://...@<tag>` instead of a relative path.

## Consequences
- Running CareerOS's stack alongside NDIP's (or any other Dockerized
  project) on the same machine no longer risks a name or port collision
  by default, and is user-fixable via `.env` if a collision still occurs.
- `docs/TechnicalDebt.md` gains an entry (TD-012) tracking Decision 2 as
  open, scoped, and explicitly deferred -- not silently forgotten.
- ADR 0002's "Consequences" section is now known to be accurate only for
  same-repository products; this ADR is the corrected reference for any
  future cross-repository product.
- No code outside `docker-compose.yml`, `.env.example`, and this
  repository's own documentation changed as a result of this ADR --
  CareerOS's application behavior is identical (confirmed: full test
  suite re-run, 12/12 passing, after the naming changes).
