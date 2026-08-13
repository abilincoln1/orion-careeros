"""
Pydantic schemas for the Document Intelligence Engine API surface
(Sprint 3 Stage 1). Mirrors the Read schema conventions established in
app/schemas/career_dna.py.
"""
import uuid
from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel

from app.models.enums import DocumentExtractionRunStatus, DocumentStatus, DocumentType


class DocumentVersionRead(BaseModel):
    id: uuid.UUID
    version_number: int
    original_filename: str
    mime_type: str
    size_bytes: int
    checksum: str
    is_current: bool
    uploaded_at: datetime

    model_config = {"from_attributes": True}


class DocumentRead(BaseModel):
    id: uuid.UUID
    person_id: uuid.UUID
    document_type: DocumentType
    status: DocumentStatus
    archived_at: Optional[datetime] = None
    created_at: datetime
    versions: List[DocumentVersionRead] = []

    model_config = {"from_attributes": True}


class DocumentExtractionRunRead(BaseModel):
    id: uuid.UUID
    document_version_id: uuid.UUID
    provider_name: str
    run_number: int
    status: DocumentExtractionRunStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    overall_confidence: Optional[float] = None
    error_detail: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    applied_at: Optional[datetime] = None
    # Full structured result, for the human review workflow -- see
    # docs/DOCUMENT-INTELLIGENCE-ARCHITECTURE.md Section 8. Typed as
    # Any rather than a strict schema here because raw_extraction_json
    # is a serialized dataclass dict (ExtractionResult), not itself a
    # Career-DNA-shaped object -- re-typing it precisely in Pydantic
    # would duplicate orion_kernel.document_intelligence.extraction_model
    # in a second, easily-drifting form.
    extraction_result: Optional[Any] = None

    model_config = {"from_attributes": True}


class ExtractionTriggerRequest(BaseModel):
    provider_name: Optional[str] = None  # None = use the configured default


class ApplySummary(BaseModel):
    """What document_intelligence_service.apply() actually did -- states
    explicitly what was written to Career DNA and what was skipped and
    why (duplicates, conflicts, defaulted fields), per this project's
    Truth First principle. TD-023 Option B: Employment and Skill are now
    applied with AI_EXTRACTED provenance; Education/Certification/
    Project/Achievement remain out of scope (no service layer exists
    for them at all yet -- a separate, larger gap than TD-023 itself,
    unaffected by this fix)."""

    person_updated: bool
    employments_applied: int
    employments_skipped_conflict: int
    skills_applied: int
    skills_skipped_duplicate: int
    note: str
