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
