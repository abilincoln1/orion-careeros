"""
Shared taxonomy upsert helper.

Implements the Architecture Review's fix for must-fix #3: taxonomy
dedup (Employer, Role, Skill, Competency, Technology all share this
"normalized_name has a unique index; insert via upsert" pattern -- see
docs/CAREER_DNA_MODEL_SPEC.md and docs/SPRINT-2-ARCHITECTURE-REVIEW.md)
must be a real `INSERT ... ON CONFLICT ... RETURNING` so the database
resolves concurrent-create races, not a service-layer "look up, then
insert if missing," which was the original design and was rejected on
review as a TOCTOU race condition.
"""
from typing import Optional, Type, TypeVar

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base

ModelType = TypeVar("ModelType", bound=Base)


def normalize(name: str) -> str:
    """Consistent normalization for every deduplicated taxonomy field
    across Employer/Role/Skill/Competency/Technology: lowercased,
    surrounding whitespace stripped, internal whitespace collapsed.
    Punctuation is deliberately left alone -- more aggressive
    normalization (e.g. stripping "Inc.") is a service-quality
    improvement for a later sprint, not a schema-correctness need."""
    return " ".join(name.strip().lower().split())


async def upsert_taxonomy(
    db: AsyncSession,
    model: Type[ModelType],
    *,
    name_field: str,
    normalized_field: str,
    name: str,
    extra_fields: Optional[dict] = None,
) -> ModelType:
    """
    Insert a taxonomy row (Employer/Role/Skill/Competency/Technology) if
    its normalized name doesn't already exist, or return the existing
    row -- as one atomic, race-free database operation, not a Python-side
    check-then-insert. Uses each backend's native upsert (Postgres
    `ON CONFLICT`, SQLite `ON CONFLICT` -- both support the same clause
    since SQLite 3.24.0, so one code path covers both of this project's
    supported test/runtime backends).
    """
    normalized = normalize(name)
    table = model.__table__
    insert_fn = pg_insert if db.bind.dialect.name == "postgresql" else sqlite_insert

    values = {name_field: name, normalized_field: normalized, **(extra_fields or {})}
    stmt = insert_fn(table).values(**values)
    stmt = stmt.on_conflict_do_nothing(index_elements=[normalized_field])
    await db.execute(stmt)

    result = await db.execute(select(model).where(getattr(model, normalized_field) == normalized))
    return result.scalar_one()
