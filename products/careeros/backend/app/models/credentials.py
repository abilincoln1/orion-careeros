"""
Career DNA Service: Education, Certification. Per
docs/CAREER_DNA_MODEL_SPEC.md §4. "Qualification" is a conceptual
supertype of these two, not a physical table -- see spec §4.3.
"""
import uuid
from datetime import date
from typing import Optional

from sqlalchemy import Boolean, Date, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.enums import DegreeLevel
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin, db_enum


class Education(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "education"

    person_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("person.id", ondelete="CASCADE"), nullable=False, index=True
    )
    institution_name: Mapped[str] = mapped_column(String(255), nullable=False)
    field_of_study: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    degree_level: Mapped[Optional[DegreeLevel]] = mapped_column(
        db_enum(DegreeLevel, "degree_level"), nullable=True
    )
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Education id={self.id} institution={self.institution_name!r}>"


class Certification(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "certification"

    person_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("person.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    issuing_organization: Mapped[str] = mapped_column(String(255), nullable=False)
    credential_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    issue_date: Mapped[date] = mapped_column(Date, nullable=False)
    expiry_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    verification_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Certification id={self.id} name={self.name!r}>"
