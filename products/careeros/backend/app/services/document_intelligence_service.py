"""
Document Intelligence orchestration service (CareerOS-side). Phases
5-7 of Sprint 3 Stage 1: upload -> storage -> extraction -> validation
-> Career DNA integration.

CRITICAL SCOPING NOTE, per TD-023 (read before modifying this file):
`apply()` only writes Person data to Career DNA. It deliberately does
NOT write Skill or Employment data yet, even though ExtractionResult
carries them and MockDocumentExtractionProvider's fixtures populate
them. This is not an oversight -- the existing, unmodified Sprint 2
services this file is required to use (`skill_service.add_person_skill`,
`employment_service.create_employment`) have no way to record
`attribution_source=AI_EXTRACTED` at all (Skill: no such parameter
exists in the service function, by design, per must-fix #5; Employment:
no such column exists on the model at all). Writing extracted skills or
employment history through those functions unmodified would silently
mislabel AI-extracted data as user-entered -- exactly the trust
violation RB-03 and ADR 0005 Decision 3 exist to prevent. See
docs/TechnicalDebt.md TD-023 for the required resolution before this
scope can expand.

This file must NEVER import Career DNA models directly (app.models.
person, app.models.employment, app.models.skills, etc.) -- only the
existing service modules. This is the TD-019 write-boundary
requirement; see tests/test_document_intelligence_boundary.py for the
enforcement mechanism.
"""
from __future__ import annotations

import uuid
from dataclasses import asdict
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from orion_kernel.document_intelligence import (
    DocumentExtractionProvider,
    ProviderFetchError,
    StorageAdapter,
    StorageValidationError,
    TextExtractionError,
    extract_text,
)
from orion_kernel.document_intelligence.storage import content_checksum

from app.models.document import Document, DocumentExtractionRun, DocumentVersion
from app.models.enums import DocumentExtractionRunStatus, DocumentStatus, DocumentType
from app.models.person import Person  # Person only -- see module docstring
from app.schemas.career_dna import PersonUpdate
from app.services import person_service


async def upload_document(
    db: AsyncSession,
    storage: StorageAdapter,
    person: Person,
    document_type: DocumentType,
    filename: str,
    content: bytes,
) -> Document:
    """Validates (via StorageAdapter.store, which runs Phase 1's file/
    MIME/size checks) and persists a new Document + its first
    DocumentVersion. Raises StorageValidationError (caller maps to 422)
    on any validation failure."""
    storage_ref = await storage.store(person.id, filename, content)  # raises StorageValidationError

    document = Document(person_id=person.id, document_type=document_type)
    db.add(document)
    await db.flush()

    version = DocumentVersion(
        document_id=document.id,
        version_number=1,
        storage_ref=storage_ref,
        original_filename=filename,
        mime_type=_mime_for(document_type),
        size_bytes=len(content),
        checksum=content_checksum(content),
        is_current=True,
    )
    db.add(version)
    await db.commit()
    await db.refresh(document)
    return document


def _mime_for(document_type: DocumentType) -> str:
    return {
        DocumentType.PDF: "application/pdf",
        DocumentType.DOCX: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }[document_type]


async def get_document_or_404(db: AsyncSession, person: Person, document_id: uuid.UUID) -> Document:
    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.person_id == person.id)
    )
    document = result.scalar_one_or_none()
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return document


async def list_documents(db: AsyncSession, person: Person) -> list[Document]:
    result = await db.execute(select(Document).where(Document.person_id == person.id))
    return list(result.scalars().all())


async def _get_current_version_or_404(db: AsyncSession, document: Document) -> DocumentVersion:
    result = await db.execute(
        select(DocumentVersion).where(
            DocumentVersion.document_id == document.id, DocumentVersion.is_current == True  # noqa: E712
        )
    )
    version = result.scalar_one_or_none()
    if version is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document has no current version")
    return version


async def extract(
    db: AsyncSession,
    storage: StorageAdapter,
    provider: DocumentExtractionProvider,
    document: Document,
) -> DocumentExtractionRun:
    """Runs the extraction pipeline (Phase 5): retrieve stored bytes,
    extract text, call the provider, persist a DocumentExtractionRun.
    Nothing here writes to Career DNA -- see apply() for that, a
    separate, explicit step."""
    version = await _get_current_version_or_404(db, document)

    existing_runs = await db.execute(
        select(DocumentExtractionRun).where(
            DocumentExtractionRun.document_version_id == version.id,
            DocumentExtractionRun.provider_name == provider.provider_name,
        )
    )
    run_number = len(existing_runs.scalars().all()) + 1

    run = DocumentExtractionRun(
        document_version_id=version.id,
        provider_name=provider.provider_name,
        run_number=run_number,
        status=DocumentExtractionRunStatus.PENDING,
    )
    db.add(run)
    await db.flush()

    try:
        content = await storage.retrieve(version.storage_ref)
        text = extract_text(document.document_type.value, content)
        result = await provider.analyze(document.document_type.value, text)
    except (TextExtractionError, ProviderFetchError) as exc:
        run.status = DocumentExtractionRunStatus.FAILED
        run.error_detail = str(exc)
        await db.commit()
        await db.refresh(run)
        return run

    run.status = DocumentExtractionRunStatus.COMPLETED
    run.overall_confidence = result.overall_confidence
    run.raw_extraction_json = _serialize_result(result)
    document.status = DocumentStatus.EXTRACTED

    await db.commit()
    await db.refresh(run)
    return run


def _serialize_result(result) -> dict:
    """dataclasses.asdict handles the nested ExtractedField wrappers and
    lists correctly; dates become `datetime.date` objects in the dict,
    which the JSON column type's default encoder cannot serialize
    directly -- converted to isoformat strings here, the one place this
    conversion needs to happen."""
    raw = asdict(result)

    def _convert(obj):
        if isinstance(obj, dict):
            return {k: _convert(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_convert(v) for v in obj]
        if hasattr(obj, "isoformat"):
            return obj.isoformat()
        return obj

    return _convert(raw)


async def get_run_or_404(
    db: AsyncSession, document: Document, run_id: uuid.UUID
) -> DocumentExtractionRun:
    result = await db.execute(
        select(DocumentExtractionRun)
        .join(DocumentVersion)
        .where(DocumentExtractionRun.id == run_id, DocumentVersion.document_id == document.id)
    )
    run = result.scalar_one_or_none()
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Extraction run not found")
    return run


async def apply(db: AsyncSession, person: Person, run: DocumentExtractionRun) -> dict:
    """
    Phase 7: Career DNA integration -- honestly scoped per TD-023 (see
    module docstring). Applies ONLY Person.headline, and only if it is
    currently unset (never overwrites a value the person already
    entered themselves with an AI-extracted guess). Returns a summary
    that explicitly states what was NOT applied and why, per this
    project's Truth First principle -- an apply() that silently no-ops
    on skills/employment without saying so would be misleading.
    """
    if run.status != DocumentExtractionRunStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot apply a run with status={run.status.value}",
        )
    if run.applied_at is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Run already applied")

    extraction = run.raw_extraction_json or {}
    persons = extraction.get("persons") or []
    skills = extraction.get("skills") or []
    employments = extraction.get("employments") or []

    person_updated = False
    if persons:
        extracted_headline = (persons[0].get("headline") or {}).get("value")
        if extracted_headline and not person.headline:
            await person_service.update_person(
                db, person.user_id, PersonUpdate(headline=extracted_headline)
            )
            person_updated = True

    from sqlalchemy import func as _func  # local import to avoid unused import when unreachable

    run.applied_at = _func.now()
    await db.commit()
    await db.refresh(run)

    return {
        "person_updated": person_updated,
        "skills_applied": 0,
        "skills_skipped_duplicate": 0,
        "employments_extracted_not_applied": len(employments),
        "note": (
            f"{len(skills)} extracted skill(s) and {len(employments)} extracted "
            "employment record(s) were NOT written to Career DNA. Neither "
            "skill_service.add_person_skill() nor employment_service."
            "create_employment() currently support recording AI-extracted "
            "provenance (see docs/TechnicalDebt.md TD-023) -- applying them "
            "unmodified would silently mislabel this data as user-entered. "
            "Blocked pending a reviewed Sprint 2 service-signature change."
        ),
    }
