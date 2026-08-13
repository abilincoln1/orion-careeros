"""
Career DNA Service: Employer, Role, Employment.

Per docs/CAREER_DNA_MODEL_SPEC.md §2. Employer/Role are platform-owned,
deduplicated taxonomy (unique index on normalized_name/normalized_title,
populated via upsert at the service layer -- see spec §2.1/§2.2 for why
a service-layer "look up then insert" alone was rejected during
architecture review as a race condition).
"""
import uuid
from datetime import date
from typing import Optional

from sqlalchemy import Boolean, Date, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import AttributionSource, EmployerSizeRange, EmploymentType, SeniorityLevel
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin, db_enum


class Employer(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "employer"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    industry_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("industry.id", ondelete="RESTRICT"), nullable=True
    )
    website: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    size_range: Mapped[Optional[EmployerSizeRange]] = mapped_column(
        db_enum(EmployerSizeRange, "employer_size_range"), nullable=True
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Employer id={self.id} name={self.name!r}>"


class Role(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "role"

    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    normalized_title: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    seniority_level: Mapped[Optional[SeniorityLevel]] = mapped_column(
        db_enum(SeniorityLevel, "seniority_level"), nullable=True
    )
    occupation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("occupation.id", ondelete="RESTRICT"), nullable=True
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Role id={self.id} title={self.title!r}>"


class Employment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "employment"
    __table_args__ = (
        # Architecture review fix: at most one *primary* (full-time or
        # part-time) current employment per person, enforced at the DB
        # level via a partial unique index -- concurrent contract/
        # freelance employments are unrestricted (spec §2.3).
        # Found via real dual-backend verification (Sprint 2): SQLite
        # silently ignores a bare `postgresql_where`-only partial index,
        # creating a full unique index on person_id instead -- which
        # would have limited every person to exactly one Employment row
        # ever, in every SQLite-backed test. SQLite has supported partial
        # indexes since 3.8.0, so the fix is simply to declare the
        # dialect-specific clause for both dialects, not to drop the
        # partial-index approach.
        Index(
            "ux_employment_one_primary_current_per_person",
            "person_id",
            unique=True,
            postgresql_where=text(
                "is_current AND employment_type IN ('full_time','part_time')"
            ),
            sqlite_where=text(
                "is_current AND employment_type IN ('full_time','part_time')"
            ),
        ),
    )

    person_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("person.id", ondelete="CASCADE"), nullable=False, index=True
    )
    employer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employer.id", ondelete="RESTRICT"), nullable=False
    )
    role_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("role.id", ondelete="RESTRICT"), nullable=True
    )
    role_title_raw: Mapped[str] = mapped_column(String(255), nullable=False)
    # Architecture review fix: promotions/title changes at the same
    # employer are always a new Employment row, chained via this FK --
    # never an in-place edit of role_id/role_title_raw on the prior row
    # (that would silently overwrite history). See spec §2.3.
    previous_employment_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employment.id", ondelete="SET NULL"), nullable=True
    )
    employment_type: Mapped[EmploymentType] = mapped_column(
        db_enum(EmploymentType, "employment_type"), nullable=False
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # TD-023 Option B (narrow fix, authorised scope -- see
    # docs/TD-023-RESOLUTION-REPORT.md and the MVP Priority 1
    # authorisation): Employment previously had no provenance concept at
    # all. Mirrors PersonSkill/PersonCompetency/PersonTechnology's
    # existing attribution_source column exactly -- same enum, same
    # default, same must-fix #5 protection (never exposed on
    # EmploymentCreate/EmploymentUpdate; only settable via an explicit
    # service-layer parameter, used by document_intelligence_service,
    # never by the public API).
    attribution_source: Mapped[AttributionSource] = mapped_column(
        db_enum(AttributionSource, "attribution_source"),
        nullable=False,
        default=AttributionSource.SELF_REPORTED,
        server_default=AttributionSource.SELF_REPORTED.value,
    )

    employer: Mapped["Employer"] = relationship(foreign_keys=[employer_id], lazy="joined")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Employment id={self.id} person_id={self.person_id} role={self.role_title_raw!r}>"
