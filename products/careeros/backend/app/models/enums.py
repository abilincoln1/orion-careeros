"""
Career DNA Service: shared enum types.

Centralized so the same Python enum backs the same PostgreSQL enum type
everywhere it's reused across models (e.g. `ProficiencyLevel` is used by
PersonSkill, PersonCompetency, and PersonTechnology alike) -- one
definition, one migration-managed DB type, per enum concept.
"""
import enum


class AttributionSource(str, enum.Enum):
    SELF_REPORTED = "self_reported"
    INFERRED = "inferred"
    VERIFIED = "verified"
    # Added Sprint 3 Stage 1 (ADR 0005 Decision 3, ADR 0006), for the
    # Document Intelligence Engine. NOT a rename of SELF_REPORTED/
    # INFERRED: those two are load-bearing for existing, accepted,
    # tagged (v0.2.0-sprint2) evidence-linking logic in
    # evidence_service.py, which explicitly demotes VERIFIED ->
    # INFERRED (never to SELF_REPORTED) when the last EvidenceLink is
    # removed -- there is no value in the Chief Architect's approved
    # provenance list (USER_ENTERED/AI_EXTRACTED/IMPORTED/VERIFIED)
    # that plays INFERRED's role, and renaming SELF_REPORTED to
    # USER_ENTERED would be a breaking, unreviewed change to Sprint 2's
    # accepted schema. Filed as TD-022 pending Chief Architect
    # confirmation of how (or whether) to reconcile the two sets rather
    # than silently deciding either way -- see docs/TechnicalDebt.md.
    AI_EXTRACTED = "ai_extracted"
    IMPORTED = "imported"


class DocumentType(str, enum.Enum):
    """Stage 1 supports exactly two; extended by migration when a new
    document type (cover letter, certificate, etc.) is authorized --
    see docs/DOCUMENT-INTELLIGENCE-ARCHITECTURE.md Section 2."""
    PDF = "pdf"
    DOCX = "docx"


class DocumentStatus(str, enum.Enum):
    """The Chief Architect's approved Document Lifecycle, exactly as
    specified: Uploaded -> Extracted -> Validated -> Imported ->
    Archived. Distinct from DocumentExtractionRunStatus, which tracks
    an individual extraction attempt, not the document as a whole."""
    UPLOADED = "uploaded"
    EXTRACTED = "extracted"
    VALIDATED = "validated"
    IMPORTED = "imported"
    ARCHIVED = "archived"


class DocumentExtractionRunStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class ProficiencyLevel(str, enum.Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class EmploymentType(str, enum.Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    FREELANCE = "freelance"
    INTERNSHIP = "internship"


class SeniorityLevel(str, enum.Enum):
    INTERN = "intern"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    PRINCIPAL = "principal"
    EXECUTIVE = "executive"


class SkillType(str, enum.Enum):
    SOFT = "soft"
    DOMAIN = "domain"
    TECHNICAL = "technical"


class TechnologyCategory(str, enum.Enum):
    LANGUAGE = "language"
    FRAMEWORK = "framework"
    TOOL = "tool"
    PLATFORM = "platform"
    DATABASE = "database"
    OTHER = "other"


class DegreeLevel(str, enum.Enum):
    HIGH_SCHOOL = "high_school"
    ASSOCIATE = "associate"
    BACHELOR = "bachelor"
    MASTER = "master"
    DOCTORATE = "doctorate"
    PROFESSIONAL = "professional"
    OTHER = "other"


class PublicationType(str, enum.Enum):
    ARTICLE = "article"
    PAPER = "paper"
    PATENT = "patent"
    TALK = "talk"
    BOOK = "book"
    OTHER = "other"


class PortfolioEntityType(str, enum.Enum):
    PROJECT = "project"
    PUBLICATION = "publication"
    ACHIEVEMENT = "achievement"


class EvidenceType(str, enum.Enum):
    URL = "url"
    DOCUMENT = "document"
    TESTIMONIAL = "testimonial"
    METRIC = "metric"
    MEDIA = "media"


class EvidenceSubjectType(str, enum.Enum):
    PERSON_SKILL = "person_skill"
    PERSON_COMPETENCY = "person_competency"
    PERSON_TECHNOLOGY = "person_technology"
    CERTIFICATION = "certification"
    EDUCATION = "education"
    PROJECT = "project"
    ACHIEVEMENT = "achievement"
    PUBLICATION = "publication"
    REFERENCE = "reference"


class CareerGoalType(str, enum.Enum):
    ROLE = "role"
    INDUSTRY = "industry"
    SKILL_DEVELOPMENT = "skill_development"
    SALARY = "salary"
    OTHER = "other"


class GoalPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class GoalStatus(str, enum.Enum):
    ACTIVE = "active"
    ACHIEVED = "achieved"
    ABANDONED = "abandoned"


class LocationPreferenceType(str, enum.Enum):
    REMOTE = "remote"
    HYBRID = "hybrid"
    ONSITE = "onsite"


class CompanySizePreference(str, enum.Enum):
    STARTUP = "startup"
    SCALEUP = "scaleup"
    MIDSIZE = "midsize"
    ENTERPRISE = "enterprise"
    NO_PREFERENCE = "no_preference"


class SalaryPeriod(str, enum.Enum):
    ANNUAL = "annual"
    MONTHLY = "monthly"
    HOURLY = "hourly"
    DAILY_RATE = "daily_rate"


class CareerStage(str, enum.Enum):
    ENTRY = "entry"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    EXECUTIVE = "executive"


class CareerStageSource(str, enum.Enum):
    SELF_REPORTED = "self_reported"
    DERIVED = "derived"


class ProfileVisibility(str, enum.Enum):
    PRIVATE = "private"
    PLATFORM = "platform"


class EmployerSizeRange(str, enum.Enum):
    R1_10 = "1-10"
    R11_50 = "11-50"
    R51_200 = "51-200"
    R201_1000 = "201-1000"
    R1001_5000 = "1001-5000"
    R5001_PLUS = "5001+"


class JobSalaryPeriod(str, enum.Enum):
    """Job Discovery (MVP Priority 2 slice). A distinct enum from the
    pre-existing SalaryPeriod (used by SalaryPreference.period,
    annual/monthly/hourly/daily_rate) -- deliberately not reused,
    because a person's stated salary preference and an external job
    listing's provider-reported pay period are genuinely different
    domain concepts that happen to share a name, not the same thing.
    A real duplicate class named SalaryPeriod was mistakenly added here
    first, silently shadowing the original and causing a genuine
    latent value mismatch (caught only because the resulting DB type
    name collision crashed loudly) -- corrected to this distinctly-
    named type instead of reusing or renaming the original."""
    YEARLY = "yearly"
    DAILY = "daily"
    HOURLY = "hourly"
