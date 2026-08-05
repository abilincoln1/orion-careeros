"""
Employment service.

Implements the Architecture Review's must-fix #1 as actual, callable
behavior: a promotion/title change at the same employer is ALWAYS a new
Employment row chained via previous_employment_id, never an in-place
edit of role_title_raw on the existing row. `promote_employment` is the
only supported way to change a person's role at an employer they're
already employed by -- EmploymentUpdate (see app/schemas/career_dna.py)
deliberately excludes role/title fields so this can't be bypassed by a
generic PATCH.

Also implements the DB-level "one primary current employment" partial
unique index (see app/models/employment.py) being surfaced as a clean
409, not a raw 500 from an uncaught IntegrityError.
"""
import uuid
from typing import Optional, Sequence

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employment import Employer, Employment
from app.models.person import Person
from app.repositories.taxonomy import upsert_taxonomy
from app.schemas.career_dna import EmploymentCreate, EmploymentPromote, EmploymentUpdate



def _is_primary_current_conflict(exc: IntegrityError) -> bool:
    """
    True if this IntegrityError is the 'one primary current employment per
    person' partial unique index (ux_employment_one_primary_current_per_person)
    being violated, False for any other integrity error (so callers still
    re-raise anything unexpected instead of silently swallowing it).

    Checked against BOTH dialects' actual error message formats, found via
    real Sprint 1.6 test execution against SQLite:
    - PostgreSQL includes the constraint/index name directly, e.g.
      '...violates unique constraint "ux_employment_one_primary_current_per_person"'.
    - SQLite does NOT include the index name at all; it reports
      'UNIQUE constraint failed: employment.person_id' -- the column, not
      the index. A check for only the index-name substring (the original
      implementation) therefore silently failed to match under SQLite,
      letting the raw IntegrityError escape as an unhandled 500 instead of
      the intended 409, even though the identical scenario correctly
      returned 409 against PostgreSQL. This is exactly the kind of
      dialect-specific gap governance/DEFINITION_OF_DONE.md's dual-backend
      testing principle exists to catch.
    """
    message = str(exc.orig)
    return "ux_employment_one_primary_current_per_person" in message or "employment.person_id" in message


async def create_employment(db: AsyncSession, person: Person, payload: EmploymentCreate) -> Employment:
    employer = await upsert_taxonomy(
        db, Employer, name_field="name", normalized_field="normalized_name", name=payload.employer_name
    )

    employment = Employment(
        person_id=person.id,
        employer_id=employer.id,
        role_title_raw=payload.role_title,
        employment_type=payload.employment_type,
        start_date=payload.start_date,
        end_date=payload.end_date,
        is_current=payload.is_current,
        description=payload.description,
    )
    db.add(employment)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        if _is_primary_current_conflict(exc):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Person already has a primary (full-time/part-time) current employment. "
                "End it first, or mark this one as not current.",
            ) from exc
        raise
    await db.refresh(employment)
    return employment


async def get_employment_or_404(db: AsyncSession, person: Person, employment_id: uuid.UUID) -> Employment:
    # Employment.employer uses lazy="joined" (see app/models/employment.py),
    # so .employer is already populated here with no extra query.
    result = await db.execute(
        select(Employment).where(Employment.id == employment_id, Employment.person_id == person.id)
    )
    employment = result.scalar_one_or_none()
    if employment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employment not found")
    return employment


async def list_employments(
    db: AsyncSession, person: Person, *, offset: int, limit: int, is_current: Optional[bool] = None
) -> tuple[Sequence[Employment], int]:
    from sqlalchemy import func

    stmt = select(Employment).where(Employment.person_id == person.id)
    count_stmt = select(func.count()).select_from(Employment).where(Employment.person_id == person.id)
    if is_current is not None:
        stmt = stmt.where(Employment.is_current == is_current)
        count_stmt = count_stmt.where(Employment.is_current == is_current)
    stmt = stmt.order_by(Employment.start_date.desc()).offset(offset).limit(limit)

    rows = (await db.execute(stmt)).scalars().all()
    total = (await db.execute(count_stmt)).scalar_one()
    return rows, total


async def update_employment(
    db: AsyncSession, person: Person, employment_id: uuid.UUID, payload: EmploymentUpdate
) -> Employment:
    """Corrections only -- see the module docstring and
    app/schemas/career_dna.py's EmploymentUpdate for why role/title
    fields are intentionally not editable here."""
    employment = await get_employment_or_404(db, person, employment_id)
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(employment, field, value)
    await db.commit()
    await db.refresh(employment)
    return employment


async def promote_employment(
    db: AsyncSession, person: Person, employment_id: uuid.UUID, payload: EmploymentPromote
) -> Employment:
    """
    Records a promotion/title change at the same employer as a NEW
    Employment row, chained to the prior one via previous_employment_id,
    with the prior row closed out (end_date/is_current updated) in the
    same transaction. This is the only code path that changes a person's
    role at an employer -- see the module docstring.
    """
    prior = await get_employment_or_404(db, person, employment_id)

    if payload.effective_date < prior.start_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="effective_date cannot be before the prior employment's start_date",
        )

    prior.end_date = payload.effective_date
    prior.is_current = False

    new_employment = Employment(
        person_id=person.id,
        employer_id=prior.employer_id,
        role_title_raw=payload.new_role_title,
        employment_type=payload.employment_type or prior.employment_type,
        start_date=payload.effective_date,
        is_current=True,
        previous_employment_id=prior.id,
    )
    db.add(new_employment)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        if _is_primary_current_conflict(exc):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Person already has a different primary current employment.",
            ) from exc
        raise
    await db.refresh(new_employment)
    return new_employment


async def delete_employment(db: AsyncSession, person: Person, employment_id: uuid.UUID) -> None:
    employment = await get_employment_or_404(db, person, employment_id)
    await db.delete(employment)
    await db.commit()
