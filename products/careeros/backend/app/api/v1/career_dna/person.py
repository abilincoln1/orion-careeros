"""Person / CareerProfile endpoints."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_person, get_current_user
from app.core.database import get_db
from app.models.person import Person
from app.models.user import User
from app.schemas.career_dna import CareerProfileRead, CareerProfileUpdate, PersonCreate, PersonRead, PersonUpdate
from app.services import person_service

router = APIRouter(prefix="/person", tags=["career-dna:person"])


@router.post("", response_model=PersonRead, status_code=status.HTTP_201_CREATED)
async def create_person(
    payload: PersonCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Person:
    return await person_service.create_person(db, current_user.id, payload)


@router.get("/me", response_model=PersonRead)
async def read_person(current_person: Person = Depends(get_current_person)) -> Person:
    return current_person


@router.patch("/me", response_model=PersonRead)
async def update_person(
    payload: PersonUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Person:
    return await person_service.update_person(db, current_user.id, payload)


@router.get("/me/profile", response_model=CareerProfileRead)
async def read_career_profile(
    current_person: Person = Depends(get_current_person),
    db: AsyncSession = Depends(get_db),
):
    return await person_service.get_career_profile_or_404(db, current_person)


@router.patch("/me/profile", response_model=CareerProfileRead)
async def update_career_profile(
    payload: CareerProfileUpdate,
    current_person: Person = Depends(get_current_person),
    db: AsyncSession = Depends(get_db),
):
    return await person_service.update_career_profile(db, current_person, payload)
