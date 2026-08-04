"""
Career DNA Service: Person (identity root) and CareerProfile (aggregate
summary), per docs/CAREER_DNA_MODEL_SPEC.md §1.

Person is 1:1 with User (Sprint 1 auth identity) today; the FK lives on
Person specifically so a future 1:many relaxation (one User managing
multiple Person records) doesn't require redirecting the FK -- see the
spec for the full rationale.
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import CareerStage, CareerStageSource, ProfileVisibility
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin, db_enum


class Person(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "person"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    preferred_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    headline: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    career_profile: Mapped["CareerProfile"] = relationship(
        back_populates="person", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Person id={self.id} name={self.first_name!r} {self.last_name!r}>"


class CareerProfile(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "career_profile"

    person_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("person.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    career_stage: Mapped[Optional[CareerStage]] = mapped_column(
        db_enum(CareerStage, "career_stage"), nullable=True
    )
    career_stage_source: Mapped[CareerStageSource] = mapped_column(
        db_enum(CareerStageSource, "career_stage_source"),
        nullable=False,
        default=CareerStageSource.SELF_REPORTED,
        server_default=CareerStageSource.SELF_REPORTED.value,
    )
    # Server-computed only -- never accepted directly from a CRUD payload
    # (enforced in the service layer, not the ORM). See spec §1.2.
    total_experience_months: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    primary_industry_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("industry.id", ondelete="RESTRICT"), nullable=True
    )
    visibility: Mapped[ProfileVisibility] = mapped_column(
        db_enum(ProfileVisibility, "profile_visibility"),
        nullable=False,
        default=ProfileVisibility.PRIVATE,
        server_default=ProfileVisibility.PRIVATE.value,
    )
    last_reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    person: Mapped["Person"] = relationship(back_populates="career_profile")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<CareerProfile id={self.id} person_id={self.person_id}>"


class CareerProfileSnapshot(Base, UUIDPrimaryKeyMixin):
    """
    Point-in-time copy of a CareerProfile's aggregate state, taken on an
    explicit snapshot service call (not automatically on every edit).
    This is the model's one deliberate full-versioning mechanism -- see
    docs/CAREER_DNA_MODEL_SPEC.md §9 for why every other entity relies on
    the fact-entity-in-place-update pattern instead of a per-table
    history log.
    """
    __tablename__ = "career_profile_snapshot"

    career_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("career_profile.id", ondelete="CASCADE"), nullable=False
    )
    snapshot_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    taken_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<CareerProfileSnapshot id={self.id} career_profile_id={self.career_profile_id}>"
