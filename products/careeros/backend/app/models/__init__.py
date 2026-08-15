from app.models.user import User  # noqa: F401

# Career DNA Service (Sprint 2) -- import order matters only for human
# readability here; SQLAlchemy resolves table creation order from FK
# dependencies via Base.metadata, not from import order.
from app.models.taxonomy import Industry, JobFamily, Occupation  # noqa: F401
from app.models.person import CareerProfile, CareerProfileSnapshot, Person  # noqa: F401
from app.models.employment import Employer, Employment, Role  # noqa: F401
from app.models.skills import (  # noqa: F401
    Competency,
    CompetencySkill,
    PersonCompetency,
    PersonSkill,
    PersonTechnology,
    Skill,
    Technology,
)
from app.models.credentials import Certification, Education  # noqa: F401
from app.models.work_product import (  # noqa: F401
    Achievement,
    PortfolioItem,
    Project,
    ProjectSkill,
    ProjectTechnology,
    Publication,
)
from app.models.evidence import Evidence, EvidenceLink, Reference  # noqa: F401
from app.models.preferences import (  # noqa: F401
    CareerGoal,
    LocationPreference,
    SalaryPreference,
    WorkPreference,
)

# Document Intelligence Engine (Sprint 3 Stage 1) -- see
# docs/DOCUMENT-INTELLIGENCE-ARCHITECTURE.md and ADR 0006.
from app.models.document import Document, DocumentExtractionRun, DocumentVersion  # noqa: F401

# Job Discovery (MVP Priority 2 slice) -- see
# docs/LEAN-JOB-DISCOVERY-IMPLEMENTATION-PLAN.md.
from app.models.job import JobListing, JobProvider  # noqa: F401
