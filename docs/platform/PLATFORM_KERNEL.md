# ORION Platform Kernel

The Platform Kernel is the set of shared, product-agnostic engineering
capabilities that every ORION Platform product consumes rather than
reimplements. CareerOS is the first product; this document is written so
that a second product could be added without guessing which capabilities
are shared and which are CareerOS-specific.

Each capability below is marked **Implemented** (real code exists under
`platform/kernel/orion_kernel`, consumed today by CareerOS) or
**Documented** (a defined responsibility and boundary, deliberately not
yet built -- implementing it is out of scope until a sprint authorises
it, per the Chief Architect directive that this document exists partly
to satisfy).

## Implemented

### Authentication
Password hashing (bcrypt) and JWT access/refresh token issuance and
verification. Lives in `orion_kernel.security`, parametrized by the
calling product's own secret key, algorithm, and expiry settings so no
product hardcodes crypto policy. CareerOS's `app/core/security.py` binds
this to its own `Settings`. Does not include SSO/OAuth against external
identity providers -- see Technical Debt.

### Authorization
**Documented only, not implemented.** The kernel currently identifies
*who* a request is from (Authentication) but does not yet enforce
role-based or scope-based permissions on *what* they can do. Every ORION
product will need this before any multi-user or multi-tenant phase.
Tracked in `docs/TechnicalDebt.md` and `docs/RiskRegister.md`.

### Configuration
`orion_kernel.config.OrionBaseSettings`: the base Pydantic settings class
every product subclasses. Holds every field common across products
(server, database, auth, CORS, logging); products override only their own
defaults (e.g. `APP_NAME`) and add product-specific fields (CareerOS adds
none yet -- domain configuration like salary bands is documented in
`config/config.example.yaml` but not implemented). `make_settings_getter`
gives each product its own cached accessor without sharing cache state
across products.

### Logging
`orion_kernel.logging`: structured logging (JSON or plain-text, chosen
per-product via `LOG_JSON`), with request ID / path / method / status /
duration fields when present. `configure_logging(settings)` is called
once per product at startup.

### Health Monitoring
`orion_kernel.health.build_health_router(settings, get_db)`: returns an
`APIRouter` providing `/health`, `/health/live`, `/health/ready` with
identical semantics for any product that calls it, including the DB
connectivity check for readiness (`orion_kernel.database.check_database_connection`).

### Request Middleware (not separately listed in the directive, but part
of the same shared-infrastructure category)
`orion_kernel.middleware.RequestContextMiddleware`: request ID + timing +
status logging, identical across products.

### Database (construction only)
`orion_kernel.database`: `make_engine`, `make_session_factory`,
`make_get_db_dependency` -- the *construction* of a product's async
engine/session/dependency is shared; each product still owns its own
`Base`, models, and migrations. This isn't one of the fifteen named
responsibilities but underlies several of them (Audit, Monitoring would
both read from product databases via this same pattern).

## Documented (not yet implemented)

These are real, intended Platform Kernel responsibilities. None has code
today. Each will be implemented as its own module or service only when a
sprint explicitly authorises it -- adding any of these speculatively
would violate the scope discipline this directive imposes.

### Secrets
A dedicated secrets-management boundary (beyond "read from environment
variables," which is what every product does today via `Configuration`).
Needed before any deployment target that isn't a single trusted local
Docker host.

### Connector Framework
The shared base for the Job Intelligence connector architecture specified
for CareerOS (fetch / validate / normalise / deduplicate / health-status
per source, with connector failure isolated from the rest of the
platform). Reserved location: `platform/shared_connectors/`. Not
authorised for implementation (Job Intelligence is explicitly excluded
from Sprint 1 Closure).

### Notifications
Cross-product outbound notification dispatch (the delivery mechanism
behind CareerOS's Communication Hub, and any future product's equivalent
need). Reserved location: `platform/shared_services/`.

### Event Bus
Cross-service eventing so that, e.g., a new job posting or interview
outcome can trigger downstream work (analytics, notifications) without
tightly coupling those services together. No product currently has more
than one service, so there is nothing to decouple yet -- correctly
deferred.

### Scheduling
Shared cron-like/recurring job scheduling (e.g. periodic connector polls,
recurring digest generation). Not needed until Job Intelligence or
Analytics exist.

### Audit
An immutable record of who changed what, when -- distinct from
operational logging (`Logging`, above). Becomes important once
Authorization exists and there is something worth auditing access to.

### Monitoring
Metrics/observability beyond the liveness/readiness endpoints
`Health Monitoring` already provides (e.g. aggregated dashboards, alerting
thresholds). The Sprint 1 Closure metrics framework
(`docs/METRICS.md`, `scripts/metrics/collect_metrics.py`) is a first,
code-quality-focused step in this direction but is not the same thing as
runtime monitoring of a deployed system.

### File Storage
A shared abstraction for storing generated documents (CVs, cover letters)
and uploaded artifacts once the Document Engine exists. No product
generates or stores files yet.

### Document Engine
The shared rendering engine behind CareerOS's planned Document Generation
Service (CVs, cover letters, supporting statements, interview prep
packs). Explicitly out of scope for Sprint 1 Closure ("Do not implement
business logic").

### Communication Hub
The shared multi-channel (dashboard, email, WhatsApp, Telegram) message
composition and delivery layer specified for CareerOS, gated everywhere
by Human Approval (nothing sends automatically). Depends on
Notifications existing first.

## How a product consumes the kernel

CareerOS is the reference example. Its `app/core/*` modules are thin
bindings, not reimplementations:

| CareerOS file | Behavior | Kernel module |
|---|---|---|
| `app/core/config.py` | `class Settings(OrionBaseSettings)` | `orion_kernel.config` |
| `app/core/logging.py` | calls `configure_logging(get_settings())` | `orion_kernel.logging` |
| `app/core/security.py` | binds kernel functions to CareerOS's settings | `orion_kernel.security` |
| `app/core/database.py` | builds CareerOS's own engine/session/Base from kernel factories | `orion_kernel.database` |
| `app/middleware.py` | re-exports | `orion_kernel.middleware` |
| `app/api/v1/health.py` | calls `build_health_router(...)` | `orion_kernel.health` |

A second ORION product would follow the same pattern: depend on
`orion-kernel` (installed from `platform/kernel`), subclass
`OrionBaseSettings`, and bind the same five modules to its own settings
and database -- without touching CareerOS's code at all.
