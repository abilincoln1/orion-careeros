"""
Career DNA Service: Project, Achievement, Publication, PortfolioItem.
Per docs/CAREER_DNA_MODEL_SPEC.md §5.
"""
import uuid
from datetime import date
from typing import Optional

from sqlalchemy import Date, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.enums import PortfolioEntityType, PublicationType
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin, db_enum


class Project(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "project"

    person_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("person.id", ondelete="CASCADE"), nullable=False, index=True
    )
    employment_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employment.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    role_in_project: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    outcome: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Project id={self.id} title={self.title!r}>"


class ProjectTechnology(Base):
    """Pure join table: Project <-> Technology (spec §5.1)."""
    __tablename__ = "project_technology"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("project.id", ondelete="CASCADE"), primary_key=True
    )
    technology_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("technology.id", ondelete="RESTRICT"), primary_key=True
    )


class ProjectSkill(Base):
    """Pure join table: Project <-> Skill (spec §5.1)."""
    __tablename__ = "project_skill"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("project.id", ondelete="CASCADE"), primary_key=True
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skill.id", ondelete="RESTRICT"), primary_key=True
    )


class Achievement(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "achievement"

    person_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("person.id", ondelete="CASCADE"), nullable=False, index=True
    )
    employment_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employment.id", ondelete="SET NULL"), nullable=True
    )
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("project.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metric_value: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    metric_unit: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    achieved_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Achievement id={self.id} title={self.title!r}>"


class Publication(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "publication"

    person_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("person.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    publication_type: Mapped[PublicationType] = mapped_column(
        db_enum(PublicationType, "publication_type"), nullable=False
    )
    publisher_or_venue: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    published_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    co_authors: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Publication id={self.id} title={self.title!r}>"


class PortfolioItem(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "portfolio_item"
    __table_args__ = (
        UniqueConstraint("linked_entity_type", "linked_entity_id", name="ux_portfolio_item_linked_entity"),
    )

    person_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("person.id", ondelete="CASCADE"), nullable=False, index=True
    )
    linked_entity_type: Mapped[PortfolioEntityType] = mapped_column(
        db_enum(PortfolioEntityType, "portfolio_entity_type"), nullable=False
    )
    # Polymorphic reference, not a real FK -- validated at the service
    # layer. See docs/CAREER_DNA_MODEL_SPEC.md §5.4 and the Architecture
    # Review's orphan-cleanup rule (§6.3 of the spec).
    linked_entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    is_featured: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<PortfolioItem id={self.id} linked_entity_type={self.linked_entity_type}>"
