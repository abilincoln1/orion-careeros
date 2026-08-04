"""
Platform Kernel: base configuration.

OrionBaseSettings holds every configuration value that is common to *any*
ORION Platform product (server, database, auth/security, CORS, logging).
Individual products subclass it to add product-specific defaults or
additional fields -- they never redefine these fields themselves, so a
platform-wide config change (e.g. a new logging field) only has to be made
once, here, and every product picks it up.

Per the Engineering Constitution's "Configuration" principle, nothing of
substance is hardcoded: every field is overridable via environment
variables / .env, both at the platform level and per-product.
"""
from functools import lru_cache
from typing import Annotated, List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class OrionBaseSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Platform / application metadata ---
    APP_NAME: str = "ORION Platform Product"
    APP_VERSION: str = "0.0.0"
    ENVIRONMENT: str = "development"  # development | staging | production
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # --- Server ---
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # --- Database ---
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://orion:orion@db:5432/orion",
        description="SQLAlchemy async database URL.",
    )
    DATABASE_URL_SYNC: str = Field(
        default="postgresql+psycopg2://orion:orion@db:5432/orion",
        description="Sync database URL used by Alembic migrations.",
    )
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_ECHO: bool = False

    # --- Auth / Security (Platform Kernel: Authentication) ---
    SECRET_KEY: str = Field(
        default="CHANGE_ME_IN_PRODUCTION_this_is_not_secure",
        description="Secret key used to sign JWT access/refresh tokens.",
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # --- CORS ---
    # NoDecode is required here: pydantic-settings treats List[str] as a
    # "complex" field and, by default, tries to JSON-decode the raw
    # environment variable *before* any pydantic validator runs -- so a
    # plain comma-separated value like "http://a,http://b" (the format
    # .env.example actually uses) raised a SettingsError/JSONDecodeError
    # at the settings-source level, never reaching our _split_cors
    # validator below. NoDecode tells pydantic-settings to leave the raw
    # string alone and let the field_validator do the parsing instead.
    # Found via a real `docker compose up --build` run against this repo
    # (the env-var-from-.env-file path was not exercised by this
    # session's Docker-less verification) -- see docs/TechnicalDebt.md
    # TD-R06.
    CORS_ORIGINS: Annotated[List[str], NoDecode] = Field(default_factory=lambda: [
        "http://localhost:5173",
        "http://localhost:3000",
    ])

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def _split_cors(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # --- Logging (Platform Kernel: Logging) ---
    LOG_LEVEL: str = "INFO"
    LOG_JSON: bool = True

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"


def make_settings_getter(settings_cls):
    """
    Factory that returns a cached settings accessor bound to a specific
    product Settings subclass. Each product calls this once, at import
    time, to get its own `get_settings()`:

        # products/careeros/backend/app/core/config.py
        class Settings(OrionBaseSettings):
            APP_NAME: str = "CareerOS (Project ORION)"

        get_settings = make_settings_getter(Settings)

    Using a factory (rather than decorating a single shared function)
    keeps each product's cache independent, so instantiating CareerOS's
    settings never returns a different product's cached instance.
    """

    @lru_cache
    def _get_settings() -> settings_cls:
        return settings_cls()

    return _get_settings
