"""
Pydantic schemas for the Career DNA Service API surface (Sprint 2 core
slice: Person/CareerProfile, Employer/Employment, Skill/PersonSkill,
Evidence/EvidenceLink). Mirrors the Create/Read split already
established by app/schemas/user.py in Sprint 1.

Fields deliberately absent from *Create/*Update schemas that exist on
the ORM model are server-computed or server-derived -- see inline notes
at each such field. This is the schema-layer half of the Architecture
Review's must-fix #5 (attribution_source) and CareerProfile's
total_experience_months rule from the spec.
"""
import uuid
from datetime import date, datetime
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field, field_validator

from app.models.enums import (
    AttributionSource,
    CareerStage,
    EmploymentType,
    EvidenceSubjectType,
    EvidenceType,
    ProficiencyLevel,
    ProfileVisibility,
    SkillType,
)


# --- Person / CareerProfile ---

class PersonCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    preferred_name: Optional[str] = Field(default=None, max_length=100)
    headline: Optional[str] = Field(default=None, max_length=255)


class PersonUpdate(BaseModel):
    first_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    preferred_name: Optional[str] = Field(default=None, max_length=100)
    headline: Optional[str] = Field(default=None, max_length=255)


class PersonRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    first_name: str
    last_name: str
    preferred_name: Optional[str] = None
    headline: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CareerProfileUpdate(BaseModel):
    summary: Optional[str] = Field(default=None, max_length=4000)
    career_stage: Optional[CareerStage] = None
    visibility: Optional[ProfileVisibility] = None
    primary_industry_id: Optional[uuid.UUID] = None
    # total_experience_months is intentionally absent: spec §1.2 requires
    # it be server-computed only, never accepted from a client payload.


class CareerProfileRead(BaseModel):
    id: uuid.UUID
    person_id: uuid.UUID
    summary: Optional[str] = None
    career_stage: Optional[CareerStage] = None
    total_experience_months: Optional[int] = None
    primary_industry_id: Optional[uuid.UUID] = None
    visibility: ProfileVisibility
    last_reviewed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Employer / Employment ---

class EmployerRead(BaseModel):
    id: uuid.UUID
    name: str
    website: Optional[str] = None
    size_range: Optional[str] = None

    model_config = {"from_attributes": True}


class EmploymentCreate(BaseModel):
    employer_name: str = Field(min_length=1, max_length=255, description="Looked up/created via upsert -- see app/repositories/taxonomy.py")
    role_title: str = Field(min_length=1, max_length=255)
    employment_type: EmploymentType
    start_date: date
    end_date: Optional[date] = None
    is_current: bool = False
    description: Optional[str] = None

    @field_validator("end_date")
    @classmethod
    def end_after_start(cls, v, info):
        start = info.data.get("start_date")
        if v is not None and start is not None and v < start:
            raise ValueError("end_date must not be before start_date")
        return v


class EmploymentUpdate(BaseModel):
    """Corrections only (typos in dates/description) -- see spec §2.3.
    Role/title changes must go through the /promote endpoint, which
    creates a new chained Employment row instead of editing this one, per
    the Architecture Review's must-fix #1."""
    end_date: Optional[date] = None
    is_current: Optional[bool] = None
    description: Optional[str] = None


class EmploymentPromote(BaseModel):
    """Records a promotion/title change at the same employer: creates a
    new Employment row chained via previous_employment_id and closes out
    the prior one. See spec §2.3 and Architecture Review must-fix #1."""
    new_role_title: str = Field(min_length=1, max_length=255)
    effective_date: date
    employment_type: Optional[EmploymentType] = None  # defaults to the prior row's type if omitted


class EmploymentRead(BaseModel):
    id: uuid.UUID
    person_id: uuid.UUID
    employer_id: uuid.UUID
    employer: Optional[EmployerRead] = None
    role_title_raw: str
    previous_employment_id: Optional[uuid.UUID] = None
    employment_type: EmploymentType
    start_date: date
    end_date: Optional[date] = None
    is_current: bool
    description: Optional[str] = None
    attribution_source: AttributionSource
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Skill / PersonSkill ---

class SkillRead(BaseModel):
    id: uuid.UUID
    name: str
    skill_type: SkillType
    description: Optional[str] = None

    model_config = {"from_attributes": True}


class PersonSkillCreate(BaseModel):
    skill_name: str = Field(min_length=1, max_length=150, description="Looked up/created via upsert")
    skill_type: SkillType = Field(description="Used only if the skill doesn't already exist in the taxonomy")
    proficiency: ProficiencyLevel
    years_experience: Optional[float] = Field(default=None, ge=0, le=99.9)
    last_used_date: Optional[date] = None
    employment_id: Optional[uuid.UUID] = None
    # attribution_source is intentionally absent -- see PersonSkillRead
    # and the Architecture Review's must-fix #5. A client can never set
    # 'verified' directly; it's derived from linked Evidence.


class PersonSkillUpdate(BaseModel):
    proficiency: Optional[ProficiencyLevel] = None
    years_experience: Optional[float] = Field(default=None, ge=0, le=99.9)
    last_used_date: Optional[date] = None
    employment_id: Optional[uuid.UUID] = None


class PersonSkillRead(BaseModel):
    id: uuid.UUID
    person_id: uuid.UUID
    skill_id: uuid.UUID
    skill: Optional[SkillRead] = None
    proficiency: ProficiencyLevel
    years_experience: Optional[float] = None
    last_used_date: Optional[date] = None
    attribution_source: AttributionSource
    employment_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Evidence / EvidenceLink ---

class EvidenceCreate(BaseModel):
    evidence_type: EvidenceType
    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    source_url: Optional[str] = Field(default=None, max_length=500)


class EvidenceRead(BaseModel):
    id: uuid.UUID
    person_id: uuid.UUID
    evidence_type: EvidenceType
    title: str
    description: Optional[str] = None
    source_url: Optional[str] = None
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EvidenceLinkCreate(BaseModel):
    subject_type: EvidenceSubjectType
    subject_id: uuid.UUID


class EvidenceLinkRead(BaseModel):
    id: uuid.UUID
    evidence_id: uuid.UUID
    subject_type: EvidenceSubjectType
    subject_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Pagination envelope, shared by every list endpoint ---
# A proper Pydantic generic so each endpoint's response_model
# (e.g. Page[EmploymentRead]) produces correct, entity-specific OpenAPI
# schema instead of a loose List[BaseModel].

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: List[T]
    total: int
    offset: int
    limit: int
