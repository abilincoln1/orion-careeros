"""
The structured extraction model -- the canonical, provider-independent
contract between the Document Intelligence Engine and any consuming
product's domain services. Phase 6 of Sprint 3 Stage 1.

Every extracted value is wrapped in ExtractedField, not returned bare,
so confidence and (eventually) provenance travel WITH the data from the
moment it is extracted, per the Chief Architect's "every extracted
field must include provenance... capture extraction confidence"
requirement. These objects are deliberately plain dataclasses with no
dependency on any product's schema (e.g. no import of CareerOS's
app.schemas.career_dna) -- that is what "provider-independent" and
"reusable by future ORION products" require structurally, not just by
convention.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass
class ExtractedField(Generic[T]):
    value: T
    confidence: float  # 0.0-1.0

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"confidence must be in [0.0, 1.0], got {self.confidence}")


@dataclass
class ExtractedPerson:
    first_name: ExtractedField[str]
    last_name: ExtractedField[str]
    headline: ExtractedField[str] | None = None


@dataclass
class ExtractedEmployment:
    employer_name: ExtractedField[str]
    role_title: ExtractedField[str]
    is_current: ExtractedField[bool]
    start_date: ExtractedField[date] | None = None
    end_date: ExtractedField[date] | None = None
    description: ExtractedField[str] | None = None
    # Added TD-023 Option B: EmploymentCreate (the existing Sprint 2
    # schema) requires employment_type, which this model previously had
    # no way to carry -- discovered only when actually wiring extraction
    # through to Career DNA, not anticipated at design time. A plain
    # string, matching skill_type/category's existing pattern (matches
    # EmploymentType enum values loosely typed here deliberately, same
    # product-agnosticism reasoning as those fields -- see the note at
    # the bottom of this file). None means the source text did not
    # clearly indicate a type; the consuming product's mapping layer
    # must then apply an explicit, disclosed fallback, never a silent one.
    employment_type: ExtractedField[str] | None = None


@dataclass
class ExtractedEducation:
    institution_name: ExtractedField[str]
    field_of_study: ExtractedField[str] | None = None
    degree_level: ExtractedField[str] | None = None  # matches DegreeLevel enum values, loosely typed here deliberately -- see note below
    start_date: ExtractedField[date] | None = None
    end_date: ExtractedField[date] | None = None


@dataclass
class ExtractedSkill:
    skill_name: ExtractedField[str]
    skill_type: ExtractedField[str] | None = None  # matches SkillType enum values
    # Added TD-023 Option B, same reasoning as ExtractedEmployment.
    # employment_type above: PersonSkillCreate requires `proficiency`,
    # which this model had no way to carry. None means undetermined from
    # source text; the consuming product must apply an explicit,
    # disclosed fallback.
    proficiency: ExtractedField[str] | None = None


@dataclass
class ExtractedTechnology:
    technology_name: ExtractedField[str]
    category: ExtractedField[str] | None = None  # matches TechnologyCategory enum values


@dataclass
class ExtractedCertification:
    name: ExtractedField[str]
    issuing_organization: ExtractedField[str] | None = None
    issued_date: ExtractedField[date] | None = None


@dataclass
class ExtractedProject:
    name: ExtractedField[str]
    description: ExtractedField[str] | None = None


@dataclass
class ExtractedAchievement:
    description: ExtractedField[str]


@dataclass
class ExtractionResult:
    persons: list[ExtractedPerson] = field(default_factory=list)
    employments: list[ExtractedEmployment] = field(default_factory=list)
    educations: list[ExtractedEducation] = field(default_factory=list)
    skills: list[ExtractedSkill] = field(default_factory=list)
    technologies: list[ExtractedTechnology] = field(default_factory=list)
    certifications: list[ExtractedCertification] = field(default_factory=list)
    projects: list[ExtractedProject] = field(default_factory=list)
    achievements: list[ExtractedAchievement] = field(default_factory=list)
    overall_confidence: float = 0.0

    def __post_init__(self) -> None:
        if not 0.0 <= self.overall_confidence <= 1.0:
            raise ValueError(
                f"overall_confidence must be in [0.0, 1.0], got {self.overall_confidence}"
            )


# Note on skill_type/category/degree_level typed as ExtractedField[str]
# rather than ExtractedField[SkillType] etc.: this package must not
# import CareerOS's app.models.enums (that would violate the same
# product-agnosticism this whole package exists to preserve -- a future
# ORION product's equivalent enums would have different values). The
# consuming product's own mapping layer (CareerOS:
# document_intelligence_service.py) is responsible for parsing these
# strings against ITS OWN enum and rejecting/flagging anything that
# doesn't match during the Validation step of the pipeline -- this is a
# deliberate design choice, not an oversight, and is recorded here so
# it isn't "rediscovered" as a bug later.
