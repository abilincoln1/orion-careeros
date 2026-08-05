"""
Document Intelligence Engine domain model (CareerOS-side). Phase 2 of
Sprint 3 Stage 1.

Three entities, per the Chief Architect's approved structure:

- Document: stable identity for an uploaded document. Never re-created
  on re-upload -- see DocumentVersion.
- DocumentVersion: one uploaded file. A Document can have multiple
  versions over time (the Chief Architect's roadmap suggestion,
  incorporated now rather than deferred, since it changes the schema
  shape and is far cheaper to build in from the start than to retrofit).
  Content is checksummed so a future re-upload flow can detect an
  unchanged resubmission and skip reprocessing without a redesign.
- DocumentExtractionRun: one extraction attempt against one
  DocumentVersion by one provider. Multiple runs per version (different
  providers, or re-running after a model improves) are a first-class
  case, not an afterthought -- see docs/DOCUMENT-INTELLIGENCE-ARCHITECTURE.md
  Section 3.

Audit metadata scope, stated explicitly rather than left implicit: this
Stage 1 implementation relies on TimestampMixin (created_at/updated_at)
plus explicit lifecycle timestamps (uploaded_at, reviewed_at,
applied_at) as its audit trail -- the same pattern every other Career
DNA model uses. A dedicated audit-log table is Platform Kernel
`shared_services` Audit capability territory (reserved, not
implemented, same status as File Storage before ADR 0005 and
Scheduling before ADR 0005 Decision 2) and is out of Stage 1 scope; not
silently dropped, just not duplicated here ahead of that capability
existing.
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import DocumentExtractionRunStatus, DocumentStatus, DocumentType
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin, db_enum


class Document(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "document"

    person_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("person.id", ondelete="CASCADE"), nullable=False, index=True
    )
    document_type: Mapped[DocumentType] = mapped_column(
        db_enum(DocumentType, "document_type"), nullable=False
    )
    status: Mapped[DocumentStatus] = mapped_column(
        db_enum(DocumentStatus, "document_status"),
        nullable=False,
        default=DocumentStatus.UPLOADED,
        server_default=DocumentStatus.UPLOADED.value,
    )
    archived_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    versions: Mapped[list["DocumentVersion"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="DocumentVersion.version_number",
        lazy="selectin",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Document id={self.id} person_id={self.person_id} type={self.document_type.value}>"


class DocumentVersion(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "document_version"
    __table_args__ = (
        UniqueConstraint("document_id", "version_number", name="ux_document_version_number"),
    )

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_ref: Mapped[str] = mapped_column(String(500), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False, index=True)  # sha256 hex digest
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    document: Mapped["Document"] = relationship(back_populates="versions")
    extraction_runs: Mapped[list["DocumentExtractionRun"]] = relationship(
        back_populates="document_version", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<DocumentVersion id={self.id} document_id={self.document_id} v={self.version_number}>"


class DocumentExtractionRun(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "document_extraction_run"
    __table_args__ = (
        UniqueConstraint(
            "document_version_id", "provider_name", "run_number",
            name="ux_document_extraction_run_number",
        ),
    )

    document_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_version.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider_name: Mapped[str] = mapped_column(String(100), nullable=False)
    run_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[DocumentExtractionRunStatus] = mapped_column(
        db_enum(DocumentExtractionRunStatus, "document_extraction_run_status"),
        nullable=False,
        default=DocumentExtractionRunStatus.PENDING,
        server_default=DocumentExtractionRunStatus.PENDING.value,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    overall_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    raw_extraction_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    error_detail: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Human review workflow (Stage 1 minimum viable version, per
    # docs/DOCUMENT-INTELLIGENCE-ARCHITECTURE.md Section 8): reviewed_at
    # is set by GET .../runs/{id} being fetched for review purposes is
    # NOT auto-tracked here (a read shouldn't require a write) -- it's
    # set explicitly by whatever future review-UI action represents
    # "a human looked at this," left for a later iteration. applied_at
    # is the real, load-bearing field: nothing writes to Career DNA
    # until this is set.
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_by_person_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("person.id", ondelete="SET NULL"), nullable=True
    )
    applied_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    document_version: Mapped["DocumentVersion"] = relationship(back_populates="extraction_runs")

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<DocumentExtractionRun id={self.id} "
            f"document_version_id={self.document_version_id} provider={self.provider_name!r}>"
        )
