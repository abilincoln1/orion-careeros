"""
Career DNA Service: shared taxonomy tables (Industry, JobFamily, Occupation).

Platform-owned reference data (see docs/CAREER_DNA_MODEL_SPEC.md §8 and
§9 "Ownership"): never deleted when a Person is, restricted (not
cascaded) from deletion while anything references them. No public CRUD
API in Sprint 2 -- grown by reference/service processes, per the spec.
"""
import uuid
from typing import Optional

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Industry(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "industry"

    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False, index=True)
    parent_industry_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("industry.id", ondelete="RESTRICT"), nullable=True
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Industry id={self.id} name={self.name!r}>"


class JobFamily(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "job_family"

    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    parent_job_family_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("job_family.id", ondelete="RESTRICT"), nullable=True
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<JobFamily id={self.id} name={self.name!r}>"


class Occupation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "occupation"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    standard_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    job_family_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("job_family.id", ondelete="RESTRICT"), nullable=True
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Occupation id={self.id} name={self.name!r}>"
