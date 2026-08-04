"""
Person / CareerProfile service.

Bootstraps a Person + CareerProfile for a User (spec §1.1/§1.2) and
handles their updates. Person is not auto-created at User registration
(Sprint 1 registration only collects email/password/optional full_name,
and Person.first_name/last_name are required, not-null fields per the
spec) -- it's created explicitly via POST /career-dna/person, called by
the client immediately after registration. This is a deliberate
implementation decision, not a silent deviation from the spec's "created
automatically when a User registers": automatic *splitting* of a single
free-text full_name into first_name/last_name is fragile (titles,
suffixes, multi-word surnames) and was rejected in favor of asking for
them explicitly, once, at Career DNA setup. See docs/SPRINT-2-TECHNICAL-NOTES.md.
"""
import uuid
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.person import CareerProfile, Person
from app.schemas.career_dna import CareerProfileUpdate, PersonCreate, PersonUpdate


async def get_person_by_user_id(db: AsyncSession, user_id: uuid.UUID) -> Optional[Person]:
    result = await db.execute(select(Person).where(Person.user_id == user_id))
    return result.scalar_one_or_none()


async def get_person_or_404(db: AsyncSession, user_id: uuid.UUID) -> Person:
    person = await get_person_by_user_id(db, user_id)
    if person is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No Career DNA profile yet -- create one with POST /career-dna/person first",
        )
    return person


async def create_person(db: AsyncSession, user_id: uuid.UUID, payload: PersonCreate) -> Person:
    existing = await get_person_by_user_id(db, user_id)
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Career DNA profile already exists")

    person = Person(
        user_id=user_id,
        first_name=payload.first_name,
        last_name=payload.last_name,
        preferred_name=payload.preferred_name,
        headline=payload.headline,
    )
    db.add(person)
    await db.flush()

    # CareerProfile is created alongside Person automatically -- spec §1.2
    # ("created automatically alongside it"), unlike Person itself which
    # requires the explicit bootstrap call above.
    profile = CareerProfile(person_id=person.id)
    db.add(profile)

    await db.commit()
    await db.refresh(person)
    return person


async def update_person(db: AsyncSession, user_id: uuid.UUID, payload: PersonUpdate) -> Person:
    person = await get_person_or_404(db, user_id)
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(person, field, value)
    await db.commit()
    await db.refresh(person)
    return person


async def get_career_profile_or_404(db: AsyncSession, person: Person) -> CareerProfile:
    result = await db.execute(select(CareerProfile).where(CareerProfile.person_id == person.id))
    profile = result.scalar_one_or_none()
    if profile is None:  # pragma: no cover -- created atomically with Person, should never happen
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Career profile not found")
    return profile


async def update_career_profile(db: AsyncSession, person: Person, payload: CareerProfileUpdate) -> CareerProfile:
    profile = await get_career_profile_or_404(db, person)
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(profile, field, value)
    await db.commit()
    await db.refresh(profile)
    return profile
