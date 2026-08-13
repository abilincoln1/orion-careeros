"""
Skill / PersonSkill service.

`attribution_source` is intentionally never set from `payload` here --
PersonSkillCreate/PersonSkillUpdate (app/schemas/career_dna.py) don't
expose that field at all. It starts at the model default (self_reported)
and only evidence_service.link_evidence/unlink_evidence ever change it,
per Architecture Review must-fix #5.
"""
import uuid
from typing import Optional, Sequence

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import AttributionSource, EvidenceSubjectType, SkillType
from app.models.person import Person
from app.models.skills import PersonSkill, Skill
from app.repositories.taxonomy import upsert_taxonomy
from app.schemas.career_dna import PersonSkillCreate, PersonSkillUpdate
from app.services.evidence_service import delete_evidence_links_for_subject


async def add_person_skill(
    db: AsyncSession,
    person: Person,
    payload: PersonSkillCreate,
    *,
    attribution_source: AttributionSource = AttributionSource.SELF_REPORTED,
) -> PersonSkill:
    """
    attribution_source is deliberately NOT part of PersonSkillCreate --
    this is must-fix #5's original protection, unchanged. The only
    caller passing a non-default value is
    document_intelligence_service.apply() (AI_EXTRACTED). No HTTP
    request body can set this (TD-023 Option B applies the identical
    pattern already used here to Employment, rather than inventing a
    new mechanism).
    """
    skill = await upsert_taxonomy(
        db,
        Skill,
        name_field="name",
        normalized_field="normalized_name",
        name=payload.skill_name,
        extra_fields={"skill_type": payload.skill_type},
    )

    existing = await db.execute(
        select(PersonSkill).where(PersonSkill.person_id == person.id, PersonSkill.skill_id == skill.id)
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Person already has this skill")

    person_skill = PersonSkill(
        person_id=person.id,
        skill_id=skill.id,
        proficiency=payload.proficiency,
        years_experience=payload.years_experience,
        last_used_date=payload.last_used_date,
        employment_id=payload.employment_id,
        attribution_source=attribution_source,
    )
    db.add(person_skill)
    await db.commit()
    await db.refresh(person_skill)
    return person_skill


async def get_person_skill_or_404(db: AsyncSession, person: Person, person_skill_id: uuid.UUID) -> PersonSkill:
    result = await db.execute(
        select(PersonSkill).where(PersonSkill.id == person_skill_id, PersonSkill.person_id == person.id)
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PersonSkill not found")
    return row


async def list_person_skills(
    db: AsyncSession, person: Person, *, offset: int, limit: int, skill_type: Optional[SkillType] = None
) -> tuple[Sequence[PersonSkill], int]:
    stmt = select(PersonSkill).where(PersonSkill.person_id == person.id)
    count_stmt = select(func.count()).select_from(PersonSkill).where(PersonSkill.person_id == person.id)
    if skill_type is not None:
        stmt = stmt.join(Skill, PersonSkill.skill_id == Skill.id).where(Skill.skill_type == skill_type)
        count_stmt = count_stmt.join(Skill, PersonSkill.skill_id == Skill.id).where(Skill.skill_type == skill_type)
    stmt = stmt.offset(offset).limit(limit)

    rows = (await db.execute(stmt)).scalars().all()
    total = (await db.execute(count_stmt)).scalar_one()
    return rows, total


async def update_person_skill(
    db: AsyncSession, person: Person, person_skill_id: uuid.UUID, payload: PersonSkillUpdate
) -> PersonSkill:
    person_skill = await get_person_skill_or_404(db, person, person_skill_id)
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(person_skill, field, value)
    await db.commit()
    await db.refresh(person_skill)
    return person_skill


async def delete_person_skill(db: AsyncSession, person: Person, person_skill_id: uuid.UUID) -> None:
    person_skill = await get_person_skill_or_404(db, person, person_skill_id)
    # Orphan-cleanup rule (Architecture Review must-fix #2): delete
    # dependent EvidenceLink rows in the SAME transaction as the subject,
    # since subject_id isn't a real FK and nothing else would catch this.
    await delete_evidence_links_for_subject(db, EvidenceSubjectType.PERSON_SKILL, person_skill.id)
    await db.delete(person_skill)
    await db.commit()


async def search_skills(db: AsyncSession, *, query: Optional[str], offset: int, limit: int) -> tuple[Sequence[Skill], int]:
    """Search the shared Skill taxonomy (not person-scoped) -- used for
    autocomplete when a client is about to call add_person_skill."""
    stmt = select(Skill)
    count_stmt = select(func.count()).select_from(Skill)
    if query:
        pattern = f"%{query.lower()}%"
        stmt = stmt.where(Skill.normalized_name.like(pattern))
        count_stmt = count_stmt.where(Skill.normalized_name.like(pattern))
    stmt = stmt.order_by(Skill.name).offset(offset).limit(limit)

    rows = (await db.execute(stmt)).scalars().all()
    total = (await db.execute(count_stmt)).scalar_one()
    return rows, total
