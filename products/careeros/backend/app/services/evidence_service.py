"""
Evidence / EvidenceLink service.

Implements two Architecture Review requirements as real, executed code
(not just documented rules):

1. **Must-fix #5** (derived, not client-settable, `verified` status):
   linking/unlinking Evidence to a PersonSkill/PersonCompetency/
   PersonTechnology is the ONLY thing that changes that record's
   `attribution_source` between INFERRED and VERIFIED --
   `_recompute_attribution` is the single place this happens.
2. **The orphan-cleanup rule** (spec §6.3): `delete_evidence_links_for_subject`
   is called by every other service (skill_service, etc.) before it
   deletes a row that can be an EvidenceLink subject, in the same
   transaction as that delete -- since `subject_id` is a polymorphic
   reference, not a real FK, nothing else would catch this.
"""
import uuid
from typing import Sequence

from fastapi import HTTPException, status
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import AttributionSource, EvidenceSubjectType
from app.models.evidence import Evidence, EvidenceLink
from app.models.person import Person
from app.schemas.career_dna import EvidenceCreate, EvidenceLinkCreate

# Subject types that carry a derived attribution_source field. Kept as an
# explicit set (not "all subject types") because Certification/Education/
# Project/Achievement/Publication/Reference don't have that field at all
# -- evidence there is just supporting proof, not something that flips a
# self-reported/verified switch.
_ATTRIBUTION_BEARING_TYPES = {
    EvidenceSubjectType.PERSON_SKILL,
    EvidenceSubjectType.PERSON_COMPETENCY,
    EvidenceSubjectType.PERSON_TECHNOLOGY,
}

_SUBJECT_MODEL_BY_TYPE = {}  # populated lazily to avoid circular imports; see _subject_model()


def _subject_model(subject_type: EvidenceSubjectType):
    if not _SUBJECT_MODEL_BY_TYPE:
        from app.models.credentials import Certification, Education
        from app.models.evidence import Reference
        from app.models.skills import PersonCompetency, PersonSkill, PersonTechnology
        from app.models.work_product import Achievement, Project, Publication

        _SUBJECT_MODEL_BY_TYPE.update(
            {
                EvidenceSubjectType.PERSON_SKILL: PersonSkill,
                EvidenceSubjectType.PERSON_COMPETENCY: PersonCompetency,
                EvidenceSubjectType.PERSON_TECHNOLOGY: PersonTechnology,
                EvidenceSubjectType.CERTIFICATION: Certification,
                EvidenceSubjectType.EDUCATION: Education,
                EvidenceSubjectType.PROJECT: Project,
                EvidenceSubjectType.ACHIEVEMENT: Achievement,
                EvidenceSubjectType.PUBLICATION: Publication,
                EvidenceSubjectType.REFERENCE: Reference,
            }
        )
    return _SUBJECT_MODEL_BY_TYPE[subject_type]


async def create_evidence(db: AsyncSession, person: Person, payload: EvidenceCreate) -> Evidence:
    evidence = Evidence(
        person_id=person.id,
        evidence_type=payload.evidence_type,
        title=payload.title,
        description=payload.description,
        source_url=payload.source_url,
    )
    db.add(evidence)
    await db.commit()
    await db.refresh(evidence)
    return evidence


async def get_evidence_or_404(db: AsyncSession, person: Person, evidence_id: uuid.UUID) -> Evidence:
    result = await db.execute(select(Evidence).where(Evidence.id == evidence_id, Evidence.person_id == person.id))
    evidence = result.scalar_one_or_none()
    if evidence is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")
    return evidence


async def list_evidence(
    db: AsyncSession, person: Person, *, offset: int, limit: int
) -> tuple[Sequence[Evidence], int]:
    stmt = (
        select(Evidence)
        .where(Evidence.person_id == person.id)
        .order_by(Evidence.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    count_stmt = select(func.count()).select_from(Evidence).where(Evidence.person_id == person.id)
    rows = (await db.execute(stmt)).scalars().all()
    total = (await db.execute(count_stmt)).scalar_one()
    return rows, total


async def _get_subject_or_404(db: AsyncSession, person: Person, subject_type: EvidenceSubjectType, subject_id: uuid.UUID):
    model = _subject_model(subject_type)
    obj = await db.get(model, subject_id)
    if obj is None or getattr(obj, "person_id", None) != person.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{subject_type.value} {subject_id} not found for this person",
        )
    return obj


async def _recompute_attribution(db: AsyncSession, subject_type: EvidenceSubjectType, subject_id: uuid.UUID) -> None:
    """The only place attribution_source is set to VERIFIED or demoted
    back to INFERRED -- see the module docstring, Architecture Review
    must-fix #5. self_reported is never touched here: a record a person
    entered by hand and never had evidence for stays self_reported even
    after evidence is added and later removed, since "was once verified,
    now isn't" and "was always self-reported" are genuinely different
    facts worth distinguishing. Only records already at inferred/verified
    move between those two states based on evidence presence.
    """
    if subject_type not in _ATTRIBUTION_BEARING_TYPES:
        return
    model = _subject_model(subject_type)
    subject = await db.get(model, subject_id)
    if subject is None:
        return

    count = (
        await db.execute(
            select(func.count())
            .select_from(EvidenceLink)
            .where(EvidenceLink.subject_type == subject_type, EvidenceLink.subject_id == subject_id)
        )
    ).scalar_one()

    if count > 0:
        subject.attribution_source = AttributionSource.VERIFIED
    elif subject.attribution_source == AttributionSource.VERIFIED:
        subject.attribution_source = AttributionSource.INFERRED


async def link_evidence(
    db: AsyncSession, person: Person, evidence_id: uuid.UUID, payload: EvidenceLinkCreate
) -> EvidenceLink:
    evidence = await get_evidence_or_404(db, person, evidence_id)
    await _get_subject_or_404(db, person, payload.subject_type, payload.subject_id)

    link = EvidenceLink(evidence_id=evidence.id, subject_type=payload.subject_type, subject_id=payload.subject_id)
    db.add(link)
    await db.flush()

    await _recompute_attribution(db, payload.subject_type, payload.subject_id)

    await db.commit()
    await db.refresh(link)
    return link


async def unlink_evidence(db: AsyncSession, person: Person, evidence_id: uuid.UUID, link_id: uuid.UUID) -> None:
    evidence = await get_evidence_or_404(db, person, evidence_id)
    result = await db.execute(
        select(EvidenceLink).where(EvidenceLink.id == link_id, EvidenceLink.evidence_id == evidence.id)
    )
    link = result.scalar_one_or_none()
    if link is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence link not found")

    subject_type, subject_id = link.subject_type, link.subject_id
    await db.delete(link)
    await db.flush()

    await _recompute_attribution(db, subject_type, subject_id)
    await db.commit()


async def delete_evidence(db: AsyncSession, person: Person, evidence_id: uuid.UUID) -> None:
    """Deleting Evidence cascades its EvidenceLink rows at the DB level
    (evidence_link.evidence_id has ondelete=CASCADE -- see
    app/models/evidence.py). But that DB-level cascade doesn't run
    Python code, so any subject that was VERIFIED purely because of this
    evidence needs its attribution_source recomputed *after* the
    cascade -- fetched *before* deleting, since the links (and the
    knowledge of which subjects they pointed at) are gone once the
    DELETE executes.
    """
    evidence = await get_evidence_or_404(db, person, evidence_id)

    affected = (
        await db.execute(select(EvidenceLink).where(EvidenceLink.evidence_id == evidence.id))
    ).scalars().all()
    affected_subjects = [(link.subject_type, link.subject_id) for link in affected]

    await db.delete(evidence)
    await db.flush()  # triggers the DB-level ON DELETE CASCADE for evidence_link rows

    for subject_type, subject_id in affected_subjects:
        await _recompute_attribution(db, subject_type, subject_id)

    await db.commit()


async def delete_evidence_links_for_subject(
    db: AsyncSession, subject_type: EvidenceSubjectType, subject_id: uuid.UUID
) -> None:
    """Orphan-cleanup rule (spec §6.3, Architecture Review must-fix #2):
    call this BEFORE deleting any row that can be an EvidenceLink
    subject (PersonSkill, PersonCompetency, PersonTechnology,
    Certification, Education, Project, Achievement, Publication,
    Reference), in the same transaction as that delete. `subject_id` is
    not a real foreign key, so nothing does this automatically."""
    await db.execute(
        delete(EvidenceLink).where(EvidenceLink.subject_type == subject_type, EvidenceLink.subject_id == subject_id)
    )
