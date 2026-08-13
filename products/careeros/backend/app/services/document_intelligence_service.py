"""
Document Intelligence orchestration service (CareerOS-side). Phases
5-7 of Sprint 3 Stage 1: upload -> storage -> extraction -> validation
-> Career DNA integration.

TD-023 OPTION B (narrow fix, authorised scope -- see
docs/TD-023-RESOLUTION-REPORT.md Section 2 and the MVP Priority 1
authorisation, superseding this module's earlier scoping note):
`apply()` now writes Person, Employment, AND Skill data to Career DNA,
each via the existing service layer only
(`person_service.update_person`, `employment_service.create_employment`,
`skill_service.add_person_skill`) -- never a direct ORM write. Both
`create_employment` and `add_person_skill` gained an optional,
API-schema-invisible `attribution_source` parameter (defaulting to
`SELF_REPORTED`, matching every existing caller's behaviour exactly);
only this file ever passes `AI_EXTRACTED`. This is deliberately NOT
TD-023's Option C (no new `data_provenance` table, no repository-wide
migration) -- Employment simply gained the same `attribution_source`
column PersonSkill/Competency/Technology already had, reusing the
identical pattern rather than inventing a new one.

This file must NEVER import Career DNA models directly (app.models.
person, app.models.employment, app.models.skills, etc.) -- only the
existing service modules and Pydantic schemas. This is the TD-019
write-boundary requirement; see
tests/test_document_intelligence_boundary.py for the enforcement
mechanism.
"""
from __future__ import annotations

import uuid
from dataclasses import asdict
from datetime import date
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
from app.models.enums import (
    AttributionSource,
    DocumentExtractionRunStatus,
    DocumentStatus,
    DocumentType,
    EmploymentType,
    ProficiencyLevel,
    SkillType,
)
from app.models.person import Person  # Person only -- see module docstring
from app.schemas.career_dna import EmploymentCreate, PersonSkillCreate, PersonUpdate
from app.services import employment_service, person_service, skill_service


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
    Phase 7: Career DNA integration. TD-023 Option B (narrow fix,
    authorised scope): Employment and Skill are now applied, with
    AI_EXTRACTED provenance, via the existing service layer only --
    employment_service.create_employment and skill_service.
    add_person_skill, both extended with an optional attribution_source
    parameter that is NOT exposed on any public API schema (must-fix #5
    preserved exactly). Person.headline continues to be applied only
    when currently unset.

    Every field the extraction model cannot determine (employment_type,
    proficiency -- see extraction_model.py's TD-023 Option B notes) gets
    an explicit, disclosed fallback here, never a silent one -- the
    returned summary states exactly which fields were defaulted, for
    which records, so the mapping is auditable rather than implicit.

    Duplicate skills (already present on this Person) and a conflicting
    'primary current employment' (the existing Sprint 2 DB constraint)
    are caught and counted, not treated as apply() failures -- a
    partial, honestly-reported result is correct; aborting the whole
    apply() over one duplicate is not.
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

    employments_applied = 0
    employments_skipped_conflict = 0
    employment_type_defaulted_count = 0

    for emp in employments:
        employer_name = (emp.get("employer_name") or {}).get("value")
        role_title = (emp.get("role_title") or {}).get("value")
        if not employer_name or not role_title:
            continue  # cannot construct a valid EmploymentCreate without these

        start_date_raw = (emp.get("start_date") or {}).get("value")
        end_date_raw = (emp.get("end_date") or {}).get("value")
        is_current = (emp.get("is_current") or {}).get("value", False)

        raw_type = (emp.get("employment_type") or {}).get("value")
        try:
            employment_type = EmploymentType(raw_type) if raw_type else EmploymentType.FULL_TIME
        except ValueError:
            employment_type = EmploymentType.FULL_TIME
        if not raw_type:
            employment_type_defaulted_count += 1

        payload = EmploymentCreate(
            employer_name=employer_name,
            role_title=role_title,
            employment_type=employment_type,
            start_date=date.fromisoformat(start_date_raw) if start_date_raw else date(1900, 1, 1),
            end_date=date.fromisoformat(end_date_raw) if end_date_raw else None,
            is_current=bool(is_current),
            description=(emp.get("description") or {}).get("value"),
        )
        try:
            await employment_service.create_employment(
                db, person, payload, attribution_source=AttributionSource.AI_EXTRACTED
            )
            employments_applied += 1
        except HTTPException as exc:
            if exc.status_code == status.HTTP_409_CONFLICT:
                employments_skipped_conflict += 1
            else:
                raise

    # Same root cause as the `run` refresh below, found by the same
    # test: a conflict inside the employment loop above rolls back
    # inside employment_service, which expires every object in this
    # session -- including `person`. The skill loop immediately below
    # touches `person.id` while building a query; on an expired object
    # that triggers a synchronous implicit reload outside the
    # async/greenlet context (MissingGreenlet), not just on `run`.
    # Refreshing here, before the skill loop starts, is the actual fix;
    # refreshing `run` later at the end is a separate, still-necessary
    # instance of the identical problem.
    await db.refresh(person)

    skills_applied = 0
    skills_skipped_duplicate = 0
    proficiency_defaulted_count = 0

    for sk in skills:
        skill_name = (sk.get("skill_name") or {}).get("value")
        if not skill_name:
            continue

        raw_skill_type = (sk.get("skill_type") or {}).get("value")
        try:
            skill_type = SkillType(raw_skill_type) if raw_skill_type else SkillType.TECHNICAL
        except ValueError:
            skill_type = SkillType.TECHNICAL

        raw_proficiency = (sk.get("proficiency") or {}).get("value")
        try:
            proficiency = ProficiencyLevel(raw_proficiency) if raw_proficiency else ProficiencyLevel.INTERMEDIATE
        except ValueError:
            proficiency = ProficiencyLevel.INTERMEDIATE
        if not raw_proficiency:
            proficiency_defaulted_count += 1

        payload = PersonSkillCreate(skill_name=skill_name, skill_type=skill_type, proficiency=proficiency)
        try:
            await skill_service.add_person_skill(
                db, person, payload, attribution_source=AttributionSource.AI_EXTRACTED
            )
            skills_applied += 1
        except HTTPException as exc:
            if exc.status_code == status.HTTP_409_CONFLICT:
                skills_skipped_duplicate += 1
            else:
                raise

    # A conflict/duplicate caught in either loop above triggers a
    # rollback inside employment_service/skill_service, which expires
    # every object still attached to this session -- including `run`.
    # Touching an expired attribute synchronously afterward (a plain
    # `run.applied_at = ...` assignment) makes SQLAlchemy attempt an
    # implicit reload outside the async/greenlet context, crashing with
    # MissingGreenlet. Found via a real test
    # (test_apply_skips_employment_conflicting_with_existing_primary_current)
    # -- an explicit, awaited refresh is the correct fix, not a workaround.
    await db.refresh(run)

    from sqlalchemy import func as _func  # local import to avoid unused import when unreachable

    run.applied_at = _func.now()
    await db.commit()
    await db.refresh(run)

    notes = []
    if employment_type_defaulted_count:
        notes.append(
            f"{employment_type_defaulted_count} employment record(s) had no extractable employment_type "
            f"-- defaulted to '{EmploymentType.FULL_TIME.value}'."
        )
    if proficiency_defaulted_count:
        notes.append(
            f"{proficiency_defaulted_count} skill(s) had no extractable proficiency "
            f"-- defaulted to '{ProficiencyLevel.INTERMEDIATE.value}'."
        )
    if employments_skipped_conflict:
        notes.append(
            f"{employments_skipped_conflict} employment record(s) skipped: conflicted with an "
            "existing primary current employment (Sprint 2's one-primary-current-employment constraint)."
        )
    if skills_skipped_duplicate:
        notes.append(f"{skills_skipped_duplicate} skill(s) skipped: already present on this person.")

    return {
        "person_updated": person_updated,
        "employments_applied": employments_applied,
        "employments_skipped_conflict": employments_skipped_conflict,
        "skills_applied": skills_applied,
        "skills_skipped_duplicate": skills_skipped_duplicate,
        "note": " ".join(notes) if notes else "All extracted employment and skills applied cleanly.",
    }
