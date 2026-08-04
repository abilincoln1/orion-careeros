"""
Career DNA Service: Skill, Competency, Technology, and their
person-association join tables. Per docs/CAREER_DNA_MODEL_SPEC.md §3.

Skill/Competency/Technology are platform-owned taxonomy (deduplicated via
a unique normalized_name index + upsert, same pattern as Employer/Role --
see app/models/employment.py). A person's *possession* of one is a
separate association row (PersonSkill/PersonCompetency/PersonTechnology)
carrying proficiency, evidence-derived attribution, and optional
employment context -- never fields on the taxonomy row itself.
"""
import uuid
from datetime import date
from typing import Optional

from sqlalchemy import ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import AttributionSource, ProficiencyLevel, SkillType, TechnologyCategory
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin, db_enum


class Skill(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "skill"

    name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    normalized_name: Mapped[str] = mapped_column(String(150), nullable=False, unique=True, index=True)
    skill_type: Mapped[SkillType] = mapped_column(
        db_enum(SkillType, "skill_type"), nullable=False
    )
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Skill id={self.id} name={self.name!r}>"


class PersonSkill(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "person_skill"
    __table_args__ = (UniqueConstraint("person_id", "skill_id", name="ux_person_skill"),)

    person_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("person.id", ondelete="CASCADE"), nullable=False, index=True
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skill.id", ondelete="RESTRICT"), nullable=False
    )
    proficiency: Mapped[ProficiencyLevel] = mapped_column(
        db_enum(ProficiencyLevel, "proficiency_level"), nullable=False
    )
    years_experience: Mapped[Optional[float]] = mapped_column(Numeric(4, 1), nullable=True)
    last_used_date: Mapped[Optional[date]] = mapped_column(nullable=True)
    # Derived, not client-settable for VERIFIED -- see spec §3.2 and the
    # Architecture Review (must-fix #5). The service layer is the only
    # writer of this field's VERIFIED value.
    attribution_source: Mapped[AttributionSource] = mapped_column(
        db_enum(AttributionSource, "attribution_source"),
        nullable=False,
        default=AttributionSource.SELF_REPORTED,
        server_default=AttributionSource.SELF_REPORTED.value,
    )
    employment_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employment.id", ondelete="SET NULL"), nullable=True
    )

    skill: Mapped["Skill"] = relationship(lazy="joined")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<PersonSkill person_id={self.person_id} skill_id={self.skill_id}>"


class Competency(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "competency"

    name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    normalized_name: Mapped[str] = mapped_column(String(150), nullable=False, unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Competency id={self.id} name={self.name!r}>"


class CompetencySkill(Base):
    """Pure join table: a Competency is composed of >=1 Skills (spec §3.3)."""
    __tablename__ = "competency_skill"

    competency_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("competency.id", ondelete="CASCADE"), primary_key=True
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skill.id", ondelete="RESTRICT"), primary_key=True
    )


class PersonCompetency(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "person_competency"
    __table_args__ = (UniqueConstraint("person_id", "competency_id", name="ux_person_competency"),)

    person_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("person.id", ondelete="CASCADE"), nullable=False, index=True
    )
    competency_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("competency.id", ondelete="RESTRICT"), nullable=False
    )
    proficiency: Mapped[ProficiencyLevel] = mapped_column(
        db_enum(ProficiencyLevel, "proficiency_level"), nullable=False
    )
    attribution_source: Mapped[AttributionSource] = mapped_column(
        db_enum(AttributionSource, "attribution_source"),
        nullable=False,
        default=AttributionSource.SELF_REPORTED,
        server_default=AttributionSource.SELF_REPORTED.value,
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<PersonCompetency person_id={self.person_id} competency_id={self.competency_id}>"


class Technology(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Resolves the directive's Technology/Framework/Tool/Programming
    Language concepts into one table with a `category` discriminator --
    see spec §3.5 for the full rationale (confirmed sound on independent
    review).
    """
    __tablename__ = "technology"

    name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    normalized_name: Mapped[str] = mapped_column(String(150), nullable=False, unique=True, index=True)
    category: Mapped[TechnologyCategory] = mapped_column(
        db_enum(TechnologyCategory, "technology_category"), nullable=False
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Technology id={self.id} name={self.name!r} category={self.category}>"


class PersonTechnology(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "person_technology"
    __table_args__ = (UniqueConstraint("person_id", "technology_id", name="ux_person_technology"),)

    person_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("person.id", ondelete="CASCADE"), nullable=False, index=True
    )
    technology_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("technology.id", ondelete="RESTRICT"), nullable=False
    )
    proficiency: Mapped[ProficiencyLevel] = mapped_column(
        db_enum(ProficiencyLevel, "proficiency_level"), nullable=False
    )
    years_experience: Mapped[Optional[float]] = mapped_column(Numeric(4, 1), nullable=True)
    last_used_date: Mapped[Optional[date]] = mapped_column(nullable=True)
    attribution_source: Mapped[AttributionSource] = mapped_column(
        db_enum(AttributionSource, "attribution_source"),
        nullable=False,
        default=AttributionSource.SELF_REPORTED,
        server_default=AttributionSource.SELF_REPORTED.value,
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<PersonTechnology person_id={self.person_id} technology_id={self.technology_id}>"
