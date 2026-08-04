"""
Career DNA Service: Evidence, EvidenceLink, Reference. Per
docs/CAREER_DNA_MODEL_SPEC.md §6.

EvidenceLink is the generic, polymorphic join that attaches one Evidence
row to a claim elsewhere in the model (a PersonSkill, Achievement,
Certification, etc.) -- deliberately not a per-table evidence_id FK, so
one piece of evidence can back multiple claims and new evidence-bearing
entity types don't require an ALTER TABLE on Evidence itself. See spec
§6.1 and §6.3, including the Architecture Review's orphan-cleanup rule
(deleting a subject must delete its EvidenceLink rows in the same
transaction -- a service-layer responsibility, not enforceable via a
real FK since subject_id is polymorphic).
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, Boolean, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.enums import EvidenceSubjectType, EvidenceType
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin, db_enum


class Evidence(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "evidence"

    person_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("person.id", ondelete="CASCADE"), nullable=False, index=True
    )
    evidence_type: Mapped[EvidenceType] = mapped_column(
        db_enum(EvidenceType, "evidence_type"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    verified_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Evidence id={self.id} title={self.title!r}>"


class EvidenceLink(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "evidence_link"
    __table_args__ = (
        UniqueConstraint("evidence_id", "subject_type", "subject_id", name="ux_evidence_link_subject"),
    )

    evidence_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("evidence.id", ondelete="CASCADE"), nullable=False, index=True
    )
    subject_type: Mapped[EvidenceSubjectType] = mapped_column(
        db_enum(EvidenceSubjectType, "evidence_subject_type"), nullable=False
    )
    subject_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<EvidenceLink evidence_id={self.evidence_id} subject_type={self.subject_type} subject_id={self.subject_id}>"


class Reference(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "reference"

    person_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("person.id", ondelete="CASCADE"), nullable=False, index=True
    )
    referee_name: Mapped[str] = mapped_column(String(255), nullable=False)
    referee_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    referee_employer: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    relationship_description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    contact_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    can_contact: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    testimonial_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # No direct evidence_id FK -- corrected on independent review, see
    # spec §6.2. Evidence for a Reference's testimonial is attached via
    # EvidenceLink (subject_type='reference'), same as every other
    # evidence-bearing entity.

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Reference id={self.id} referee_name={self.referee_name!r}>"
