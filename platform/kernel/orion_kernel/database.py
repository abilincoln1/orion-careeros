"""
Platform Kernel: database engine/session factory.

Every ORION product gets its own SQLAlchemy async engine, session
factory, and declarative Base (models must not be shared across products
-- each product owns its own schema), but the *construction* of those
things -- pooling, echo, pre-ping, the get_db dependency shape -- is
common and lives here once.
"""
from typing import AsyncGenerator, Callable

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


def make_engine(settings):
    """settings must expose DATABASE_URL, DB_ECHO, DB_POOL_SIZE, DB_MAX_OVERFLOW."""
    return create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DB_ECHO,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_pre_ping=True,
    )


def make_session_factory(engine) -> async_sessionmaker:
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )


def make_get_db_dependency(session_factory: async_sessionmaker) -> Callable[[], AsyncGenerator[AsyncSession, None]]:
    """Returns a FastAPI dependency bound to a specific product's session factory."""

    async def get_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            try:
                yield session
            finally:
                await session.close()

    return get_db


async def check_database_connection(session: AsyncSession) -> bool:
    """
    Shared readiness check: takes an active session (from the product's
    own get_db dependency) so it exercises exactly the connection path
    the product actually uses at runtime, whatever the underlying
    database engine (Postgres in production, SQLite in fast local tests).
    """
    from sqlalchemy import text

    try:
        await session.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


class KernelBase(DeclarativeBase):
    """
    Convenience base products may use directly for their declarative
    models. Each product still owns its own metadata/tables -- this is
    just to avoid every product re-writing an identical one-line class.
    """
    pass
