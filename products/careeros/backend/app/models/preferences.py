"""
Career DNA Service: CareerGoal, LocationPreference, WorkPreference,
SalaryPreference. Per docs/CAREER_DNA_MODEL_SPEC.md §7.
"""
import uuid
from datetime import date
from typing import List, Optional

from sqlalchemy import JSON, Boolean, Date, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.enums import (
    CareerGoalType,
    CompanySizePreference,
    GoalPriority,
    GoalStatus,
    LocationPreferenceType,
    SalaryPeriod,
)
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin, db_enum


class CareerGoal(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "career_goal"

    person_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("person.id", ondelete="CASCADE"), nullable=False, index=True
    )
    goal_type: Mapped[CareerGoalType] = mapped_column(
        db_enum(CareerGoalType, "career_goal_type"), nullable=False
    )
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    target_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    priority: Mapped[GoalPriority] = mapped_column(
        db_enum(GoalPriority, "goal_priority"),
        nullable=False,
        default=GoalPriority.MEDIUM,
        server_default=GoalPriority.MEDIUM.value,
    )
    status: Mapped[GoalStatus] = mapped_column(
        db_enum(GoalStatus, "goal_status"),
        nullable=False,
        default=GoalStatus.ACTIVE,
        server_default=GoalStatus.ACTIVE.value,
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<CareerGoal id={self.id} goal_type={self.goal_type}>"


class LocationPreference(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "location_preference"

    person_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("person.id", ondelete="CASCADE"), nullable=False, index=True
    )
    location_text: Mapped[str] = mapped_column(String(255), nullable=False)
    preference_type: Mapped[LocationPreferenceType] = mapped_column(
        db_enum(LocationPreferenceType, "location_preference_type"), nullable=False
    )
    willing_to_relocate: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    max_commute_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    priority_rank: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<LocationPreference id={self.id} location_text={self.location_text!r}>"


class WorkPreference(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "work_preference"

    person_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("person.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    # JSON, not a native array column: portability decision (see Sprint 2
    # Technical Notes) -- sqlalchemy.dialects.postgresql.ARRAY has no
    # SQLite fallback, and this project's default fast test suite runs
    # against in-memory SQLite (see products/careeros/backend/tests/conftest.py).
    # JSON works identically against both, storing the same list of
    # EmploymentType string values described conceptually as "array(enum)"
    # in docs/CAREER_DNA_MODEL_SPEC.md §7.3.
    preferred_employment_types: Mapped[List[str]] = mapped_column(
        JSON, nullable=False, default=list, server_default="[]"
    )
    company_size_preference: Mapped[CompanySizePreference] = mapped_column(
        db_enum(CompanySizePreference, "company_size_preference"),
        nullable=False,
        default=CompanySizePreference.NO_PREFERENCE,
        server_default=CompanySizePreference.NO_PREFERENCE.value,
    )
    culture_values: Mapped[List[str]] = mapped_column(
        JSON, nullable=False, default=list, server_default="[]"
    )
    available_from: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<WorkPreference id={self.id} person_id={self.person_id}>"


class SalaryPreference(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "salary_preference"

    person_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("person.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    min_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    max_amount: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    period: Mapped[SalaryPeriod] = mapped_column(
        db_enum(SalaryPeriod, "salary_period"), nullable=False
    )
    is_negotiable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<SalaryPreference id={self.id} person_id={self.person_id}>"
