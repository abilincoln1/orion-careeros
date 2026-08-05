# Developer Guide

Practical, day-to-day reference for working on CareerOS (the first
product on the ORION Platform). For system design and the platform/product
split, see `docs/ARCHITECTURE.md`. For the full engineering standards
every change is expected to meet, see `/governance`.

## First-time setup

```powershell
git clone <this repository>
cd "Career OS"
.\scripts\bootstrap.ps1
```

`bootstrap.ps1` verifies Docker Desktop, Docker Compose, Git, and Python
(the last is optional and only warned about, not required); creates
`.env` from `.env.example` if you don't have one yet; builds and starts
the stack; runs migrations; and polls the health endpoints until the
backend is actually reachable, not just "container started."

**This works from any drive or folder name** -- `C:\Projects\Career OS`,
`D:\Development\CareerOS`, wherever you cloned it. The script resolves
all paths relative to its own location, never a hardcoded path. See
`docs/REPOSITORY_INDEPENDENCE_REPORT.md` for how that was verified.

If you already have the containers built and just want to restart:

```powershell
.\scripts\bootstrap.ps1 -SkipBuild
```

## Port collisions with other projects
This machine may run more than one project at once (e.g. NDIP). CareerOS
defaults to ports `5432` (Postgres), `8000` (backend), `5173` (frontend).
If one of those is already taken, set an override in `.env` -- no need to
touch `docker-compose.yml`:

```
POSTGRES_PORT=5433
BACKEND_PORT=8001
FRONTEND_PORT=5174
```

Then re-run `.\scripts\bootstrap.ps1`. Container, image, network, and
volume names already use the `orion-careeros-*` prefix specifically so
they never collide with another project's containers even if both stacks
run simultaneously -- see `docs/adr/0003-docker-naming-and-multi-project-isolation.md`.

## Day-to-day commands

```bash
docker compose up -d              # start everything in the background
docker compose logs -f backend    # tail backend logs
docker compose logs -f frontend   # tail frontend logs
docker compose down               # stop everything
docker compose down -v            # stop everything AND wipe the database volume
```

Backend API docs (Swagger UI): `http://localhost:8000/docs` (or whatever
`BACKEND_PORT` you set).

## Running tests

```bash
./scripts/run_tests.sh                # in-memory SQLite -- fast, no Docker/Postgres needed
./scripts/run_tests_postgres.sh       # against real Postgres -- set TEST_DATABASE_URL first
```

Both scripts install `orion_kernel` editable from the repo-relative path
automatically -- no manual pip step needed first.

## Database migrations

```bash
cd products/careeros/backend
alembic revision --autogenerate -m "describe the change"
alembic upgrade head
```

Migrations run automatically on container startup (`docker-compose.yml`'s
backend `command`) and are idempotent, so you don't need to run them by
hand in the normal workflow -- this is only for creating a *new*
migration after changing a model.

## Working on the Platform Kernel vs. the product
- `platform/kernel/orion_kernel/*` -- shared, product-agnostic code
  (config, logging, security, database, health, middleware). Changes here
  affect every current and future ORION product. Before adding anything
  here, ask: would a second, unrelated product also want this exact
  behavior? If it's CareerOS-specific, it belongs in
  `products/careeros/backend/app/*` instead.
- The kernel must never import from `app.*` (product code). This is
  mechanically checked by `scripts/metrics/collect_metrics.py`'s
  architecture-compliance check -- a static grep, not a suggestion.
- The kernel is currently only consumable by a product living inside this
  same repository (a relative editable install). It is **not** yet
  consumable by a separate repository (e.g. a future NDIP-on-ORION). This
  is tracked, not accidental -- see TD-012 and ADR 0003 before assuming
  otherwise.

## Coding standards
See `orion-governance/governance/CodingStandards.md` and `orion-governance/engineering/DefinitionOfDone.md`
for the full list. The two most load-bearing rules in practice:

- Nothing is hardcoded that should be configuration -- if you're tempted
  to hardcode a value, it probably belongs in `Settings`
  (`platform/kernel/orion_kernel/config.py` or the product's subclass).
- Every "done" claim needs a command that was actually run and its output
  actually read, per `orion-governance/engineering/DefinitionOfDone.md` -- this project's
  history (see `docs/TechnicalDebt.md`'s "Resolved" table) has repeatedly
  found real bugs specifically because verification was insisted on
  rather than assumed.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `docker compose up` fails immediately, port already in use | Another project (possibly NDIP) is using the same host port | Set `POSTGRES_PORT`/`BACKEND_PORT`/`FRONTEND_PORT` in `.env` to unused values |
| Backend container crash-loops on startup | Usually a `.env` parsing issue -- see TD-R06 for a real example (`CORS_ORIGINS`) | `docker compose logs backend` for the traceback; check the field's type/format in `platform/kernel/orion_kernel/config.py` |
| `pip install -e ../../../platform/kernel` fails outside Docker | You're not running the command from `products/careeros/backend` | `cd products/careeros/backend` first -- the path is relative to that directory |
| Tests pass locally but you're unsure about Postgres-specific behavior | SQLite (default test DB) doesn't catch every Postgres-specific issue | Run `./scripts/run_tests_postgres.sh` against a real Postgres instance before considering a change fully verified |

## Where things live

```
/platform/kernel        Shared, product-agnostic engineering primitives (orion_kernel)
/products/careeros       This product: backend (FastAPI) + frontend (React/TS/Vite)
/governance              Engineering Constitution and standards every change follows
/docs                    Architecture, API reference, ADRs, reports, registers, metrics
/scripts                 bootstrap.ps1 + Unix dev-convenience scripts
/config                  Non-secret domain configuration (placeholder for future sprints)
```

Full structure and rationale: `docs/ARCHITECTURE.md`, `README.md`.
