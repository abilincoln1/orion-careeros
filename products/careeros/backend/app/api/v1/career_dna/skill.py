"""Skill taxonomy search + PersonSkill CRUD."""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_person
from app.core.database import get_db
from app.models.enums import SkillType
from app.models.person import Person
from app.schemas.career_dna import Page, PersonSkillCreate, PersonSkillRead, PersonSkillUpdate, SkillRead
from app.services import skill_service

router = APIRouter(tags=["career-dna:skill"])


@router.get("/skills", response_model=Page[SkillRead])
async def search_skills(
    q: Optional[str] = Query(default=None, description="Substring search over the shared skill taxonomy"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    rows, total = await skill_service.search_skills(db, query=q, offset=offset, limit=limit)
    return Page[SkillRead](items=rows, total=total, offset=offset, limit=limit)


@router.post("/person-skills", response_model=PersonSkillRead, status_code=status.HTTP_201_CREATED)
async def add_person_skill(
    payload: PersonSkillCreate,
    current_person: Person = Depends(get_current_person),
    db: AsyncSession = Depends(get_db),
):
    return await skill_service.add_person_skill(db, current_person, payload)


@router.get("/person-skills", response_model=Page[PersonSkillRead])
async def list_person_skills(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    skill_type: Optional[SkillType] = Query(default=None),
    current_person: Person = Depends(get_current_person),
    db: AsyncSession = Depends(get_db),
):
    rows, total = await skill_service.list_person_skills(
        db, current_person, offset=offset, limit=limit, skill_type=skill_type
    )
    return Page[PersonSkillRead](items=rows, total=total, offset=offset, limit=limit)


@router.patch("/person-skills/{person_skill_id}", response_model=PersonSkillRead)
async def update_person_skill(
    person_skill_id: uuid.UUID,
    payload: PersonSkillUpdate,
    current_person: Person = Depends(get_current_person),
    db: AsyncSession = Depends(get_db),
):
    return await skill_service.update_person_skill(db, current_person, person_skill_id, payload)


@router.delete("/person-skills/{person_skill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_person_skill(
    person_skill_id: uuid.UUID,
    current_person: Person = Depends(get_current_person),
    db: AsyncSession = Depends(get_db),
):
    await skill_service.delete_person_skill(db, current_person, person_skill_id)
