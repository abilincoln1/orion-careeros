"""
Test configuration.

Defaults to an in-memory SQLite database (via aiosqlite) for fast, isolated
unit and API tests, so the suite does not depend on a running Postgres
instance for everyday development.

For CI / release-gate parity, the suite can instead be pointed at a real
PostgreSQL instance by setting TEST_DATABASE_URL, e.g.:

    TEST_DATABASE_URL="postgresql+asyncpg://careeros:careeros@localhost:5432/careeros_test" \
        pytest -v

This is the mechanism used for the Sprint 1 Postgres verification run
(see docs/SPRINT-1-REVIEW.md / docs/governance for results) and should be
run as part of any future CI pipeline for full-parity checks, in addition
to the fast SQLite-backed default used locally.
"""
import os
from typing import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool, StaticPool

from app.core.database import Base, get_db
from app.main import app

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL", "sqlite+aiosqlite:///:memory:")
_IS_SQLITE = TEST_DATABASE_URL.startswith("sqlite")

if _IS_SQLITE:
    test_engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # SQLite does NOT enforce FOREIGN KEY constraints -- including
    # ON DELETE CASCADE -- unless "PRAGMA foreign_keys = ON" is executed on
    # every connection. Without this, every ondelete="CASCADE" relationship
    # in the Career DNA schema (Evidence -> EvidenceLink, Person -> *, etc.)
    # silently does nothing under the SQLite test backend: rows that should
    # be cascade-deleted are left behind as orphans instead. This was found
    # via a real failing test during Sprint 1.6 (deleting Evidence did not
    # actually remove its EvidenceLink rows, so attribution_source recompute
    # saw a stale link and incorrectly stayed "verified" instead of
    # demoting to "inferred"). The application's cascade configuration
    # itself is correct; this was a test-infrastructure gap that meant the
    # fast SQLite test path could never have caught a cascade regression,
    # even though the identical scenario would behave correctly against
    # PostgreSQL (which enforces FKs by default). Registered on the sync
    # DBAPI connection via the aiosqlite dialect's underlying sqlite3
    # connection, per SQLAlchemy's documented pattern for this exact issue.
    @event.listens_for(test_engine.sync_engine, "connect")
    def _enable_sqlite_foreign_keys(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

else:
    # Real Postgres (or any non-SQLite dialect): no SQLite-only connect_args/pool.
    test_engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)

TestSessionLocal = async_sessionmaker(bind=test_engine, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True)
async def _setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = _override_get_db


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
