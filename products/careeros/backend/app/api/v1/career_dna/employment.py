"""Employment endpoints, including the dedicated /promote operation that
implements the Architecture Review's must-fix #1 (promotions are always
a new chained row, never an in-place title edit)."""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_person
from app.core.database import get_db
from app.models.person import Person
from app.schemas.career_dna import EmploymentCreate, EmploymentPromote, EmploymentRead, EmploymentUpdate, Page
from app.services import employment_service

router = APIRouter(prefix="/employments", tags=["career-dna:employment"])


@router.post("", response_model=EmploymentRead, status_code=status.HTTP_201_CREATED)
async def create_employment(
    payload: EmploymentCreate,
    current_person: Person = Depends(get_current_person),
    db: AsyncSession = Depends(get_db),
):
    return await employment_service.create_employment(db, current_person, payload)


@router.get("", response_model=Page[EmploymentRead])
async def list_employments(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    is_current: Optional[bool] = Query(default=None),
    current_person: Person = Depends(get_current_person),
    db: AsyncSession = Depends(get_db),
):
    rows, total = await employment_service.list_employments(
        db, current_person, offset=offset, limit=limit, is_current=is_current
    )
    return Page[EmploymentRead](items=rows, total=total, offset=offset, limit=limit)


@router.get("/{employment_id}", response_model=EmploymentRead)
async def get_employment(
    employment_id: uuid.UUID,
    current_person: Person = Depends(get_current_person),
    db: AsyncSession = Depends(get_db),
):
    return await employment_service.get_employment_or_404(db, current_person, employment_id)


@router.patch("/{employment_id}", response_model=EmploymentRead)
async def update_employment(
    employment_id: uuid.UUID,
    payload: EmploymentUpdate,
    current_person: Person = Depends(get_current_person),
    db: AsyncSession = Depends(get_db),
):
    return await employment_service.update_employment(db, current_person, employment_id, payload)


@router.post("/{employment_id}/promote", response_model=EmploymentRead, status_code=status.HTTP_201_CREATED)
async def promote_employment(
    employment_id: uuid.UUID,
    payload: EmploymentPromote,
    current_person: Person = Depends(get_current_person),
    db: AsyncSession = Depends(get_db),
):
    """Records a promotion/title change: creates a NEW Employment row
    chained to this one, and closes this one out. See
    app/services/employment_service.py and
    docs/SPRINT-2-ARCHITECTURE-REVIEW.md must-fix #1."""
    return await employment_service.promote_employment(db, current_person, employment_id, payload)


@router.delete("/{employment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_employment(
    employment_id: uuid.UUID,
    current_person: Person = Depends(get_current_person),
    db: AsyncSession = Depends(get_db),
):
    await employment_service.delete_employment(db, current_person, employment_id)
