"""Evidence CRUD + link/unlink to a subject elsewhere in the model."""
import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_person
from app.core.database import get_db
from app.models.person import Person
from app.schemas.career_dna import EvidenceCreate, EvidenceLinkCreate, EvidenceLinkRead, EvidenceRead, Page
from app.services import evidence_service

router = APIRouter(prefix="/evidence", tags=["career-dna:evidence"])


@router.post("", response_model=EvidenceRead, status_code=status.HTTP_201_CREATED)
async def create_evidence(
    payload: EvidenceCreate,
    current_person: Person = Depends(get_current_person),
    db: AsyncSession = Depends(get_db),
):
    return await evidence_service.create_evidence(db, current_person, payload)


@router.get("", response_model=Page[EvidenceRead])
async def list_evidence(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    current_person: Person = Depends(get_current_person),
    db: AsyncSession = Depends(get_db),
):
    rows, total = await evidence_service.list_evidence(db, current_person, offset=offset, limit=limit)
    return Page[EvidenceRead](items=rows, total=total, offset=offset, limit=limit)


@router.post("/{evidence_id}/link", response_model=EvidenceLinkRead, status_code=status.HTTP_201_CREATED)
async def link_evidence(
    evidence_id: uuid.UUID,
    payload: EvidenceLinkCreate,
    current_person: Person = Depends(get_current_person),
    db: AsyncSession = Depends(get_db),
):
    """Attaching evidence to a PersonSkill/PersonCompetency/
    PersonTechnology automatically promotes its attribution_source to
    VERIFIED -- see app/services/evidence_service.py and Architecture
    Review must-fix #5. There is no separate "mark as verified" endpoint,
    by design."""
    return await evidence_service.link_evidence(db, current_person, evidence_id, payload)


@router.delete("/{evidence_id}/link/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unlink_evidence(
    evidence_id: uuid.UUID,
    link_id: uuid.UUID,
    current_person: Person = Depends(get_current_person),
    db: AsyncSession = Depends(get_db),
):
    await evidence_service.unlink_evidence(db, current_person, evidence_id, link_id)


@router.delete("/{evidence_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_evidence(
    evidence_id: uuid.UUID,
    current_person: Person = Depends(get_current_person),
    db: AsyncSession = Depends(get_db),
):
    await evidence_service.delete_evidence(db, current_person, evidence_id)
