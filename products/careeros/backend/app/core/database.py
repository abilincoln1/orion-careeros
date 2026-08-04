"""
CareerOS database engine and session management (SQLAlchemy 2.0, async).

The engine/session-factory *construction* (pooling, echo, pre-ping, the
get_db dependency shape) is shared platform infrastructure and lives in
the ORION Platform Kernel (platform/kernel/orion_kernel/database.py).
CareerOS owns its own engine instance, session factory, and declarative
Base/metadata -- each ORION product has its own schema; only the
machinery that builds them is shared.

Per the Career Knowledge Base principle, the relational schema built here
in Sprint 1 (users/auth only) is the seed of the future Career Knowledge
Graph. No document (CV, cover letter, etc.) is ever treated as a system of
record; only structured rows/relationships are.
"""
from orion_kernel.database import (
    check_database_connection,  # re-exported as-is
    make_engine,
    make_get_db_dependency,
    make_session_factory,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings

settings = get_settings()

engine = make_engine(settings)
AsyncSessionLocal = make_session_factory(engine)
get_db = make_get_db_dependency(AsyncSessionLocal)


class Base(DeclarativeBase):
    """CareerOS's own declarative base. Each ORION product owns its own models/metadata."""
    pass


__all__ = ["engine", "AsyncSessionLocal", "Base", "get_db", "check_database_connection"]
