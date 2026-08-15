"""
CareerOS application configuration.

CareerOS's Settings is a thin product-level subclass of the ORION
Platform Kernel's OrionBaseSettings (see platform/kernel/orion_kernel/config.py).
All platform-wide fields (database, auth, logging, CORS, server) are
inherited from the kernel unchanged; this file only overrides the
defaults that are specific to CareerOS as a product, and documents the
domain configuration (salary bands, commute radius, matching weights,
etc.) that Sprint 1 intentionally does not implement yet.

Per the Engineering Constitution's "Configuration" principle, nothing of
substance is hardcoded: every field is overridable via environment
variables / .env.
"""
from orion_kernel.config import OrionBaseSettings, make_settings_getter


class Settings(OrionBaseSettings):
    # --- CareerOS-specific overrides of platform defaults ---
    APP_NAME: str = "CareerOS (Project ORION)"
    APP_VERSION: str = "0.1.0-sprint1"

    DATABASE_URL: str = "postgresql+asyncpg://careeros:careeros@db:5432/careeros"
    DATABASE_URL_SYNC: str = "postgresql+psycopg2://careeros:careeros@db:5432/careeros"

    # Domain configuration (salary bands, commute radius, contract
    # weighting, remote preference, match thresholds, company watchlists,
    # learning priorities) is deferred to the sprint that implements the
    # Matching Engine -- see config/config.example.yaml for the documented
    # shape it will take, and docs/platform/PLATFORM_KERNEL.md for how it
    # relates to platform-level configuration.

    # Document Intelligence Engine (Sprint 3 Stage 1). Local-filesystem
    # storage only -- ADR 0005 Decision 1 explicitly deferred a shared
    # Platform File Storage capability until a second product needs one.
    DOCUMENT_STORAGE_PATH: str = "/app/data/document_storage"

    # Job Discovery (MVP Priority 2 slice, Chief Architect directive
    # "Priority 1 Closure & Job Discovery", 14 August 2026). Real,
    # overridable settings -- per Section 4's explicit instruction that
    # the salary range be "a configurable CareerOS preference rather
    # than a hard-coded application constant." Used only as the
    # fallback when the person has no SalaryPreference row and no
    # per-request override is supplied -- never invented per-listing.
    DISCOVERY_DEFAULT_SALARY_MIN: int = 40000
    DISCOVERY_DEFAULT_SALARY_MAX: int = 110000
    DISCOVERY_DEFAULT_CURRENCY: str = "GBP"


get_settings = make_settings_getter(Settings)
