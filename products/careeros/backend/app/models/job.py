"""
Job Discovery domain model (MVP Priority 2 slice, Chief Architect
directive "Priority 1 Closure & Job Discovery", 14 August 2026).

Deliberately minimal, per docs/LEAN-JOB-DISCOVERY-IMPLEMENTATION-PLAN.md:
`JobProvider` has no `provider_type`/`credentials_ref` yet (one
provider, no auth needed); `JobListing` omits `company_id` and skill/
technology association tables (deferred until actually needed). This
is not the full Sprint 3 Job Intelligence design -- see that plan for
exactly what was deferred and why.

No relationship to Career DNA whatsoever: JobListing is not owned by a
Person and is never written to Career DNA. Career DNA is read from
(via job_discovery_service), never written to, by this feature.
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import JobSalaryPeriod
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin, db_enum


class JobProvider(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "job_provider"

    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    listings: Mapped[list["JobListing"]] = relationship(back_populates="provider")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<JobProvider id={self.id} name={self.name!r}>"


class JobListing(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "job_listing"
    __table_args__ = (
        UniqueConstraint("provider_id", "provider_external_id", name="ux_job_listing_provider_external_id"),
    )

    provider_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("job_provider.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider_external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    company_name_raw: Mapped[str] = mapped_column(String(500), nullable=False)
    location_raw: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_remote: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")

    # Salary: never invented. salary_disclosed is explicit, not derived
    # from whether salary_min/max happen to be NULL -- a provider could
    # in principle send an explicit "not disclosed" flag distinct from
    # simply omitting the field, and this schema doesn't conflate the two.
    salary_min: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    salary_max: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    salary_currency: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)  # ISO 4217, e.g. "GBP"
    salary_period: Mapped[Optional[JobSalaryPeriod]] = mapped_column(
        db_enum(JobSalaryPeriod, "job_salary_period"), nullable=True
    )
    salary_disclosed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")

    description_raw: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    posted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    discovered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    raw_payload_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    provider: Mapped["JobProvider"] = relationship(back_populates="listings")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<JobListing id={self.id} title={self.title!r} company={self.company_name_raw!r}>"
