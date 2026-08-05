"""
ORION Platform Kernel: Document Intelligence Engine.

A reusable capability for ingesting and interpreting professional
documents (CVs, and later cover letters, certificates, degrees,
licences, LinkedIn exports, job descriptions, references, performance
reviews, skills assessments). CareerOS is the first consumer; every
piece of this package is deliberately product-agnostic -- it knows
nothing about Career DNA, Person, or any CareerOS-specific concept.
What extracted data MEANS for a given product's domain model is that
product's own responsibility (see
products/careeros/backend/app/services/document_intelligence_service.py).

See docs/DOCUMENT-INTELLIGENCE-ARCHITECTURE.md and
docs/adr/0006-document-intelligence-engine.md for the full design and
the reasoning for placing this in the kernel rather than product-local
(the same question File Storage, ADR 0005 Decision 1, answered the
opposite way).

Stage 1 scope: storage + domain model + provider abstraction + a mock
provider. No production AI provider is integrated yet, per the Chief
Architect's explicit "prove the interface first" directive.
"""
from orion_kernel.document_intelligence.storage import (
    LocalStorageAdapter,
    StorageAdapter,
    StorageValidationError,
)
from orion_kernel.document_intelligence.provider import (
    DocumentExtractionProvider,
    ProviderFetchError,
)
from orion_kernel.document_intelligence.text_extraction import extract_text, TextExtractionError
from orion_kernel.document_intelligence.mock_provider import MockDocumentExtractionProvider
from orion_kernel.document_intelligence.extraction_model import (
    ExtractedAchievement,
    ExtractedCertification,
    ExtractedEducation,
    ExtractedEmployment,
    ExtractedField,
    ExtractedPerson,
    ExtractedProject,
    ExtractedSkill,
    ExtractedTechnology,
    ExtractionResult,
)

__all__ = [
    "StorageAdapter",
    "LocalStorageAdapter",
    "StorageValidationError",
    "DocumentExtractionProvider",
    "ProviderFetchError",
    "MockDocumentExtractionProvider",
    "extract_text",
    "TextExtractionError",
    "ExtractedField",
    "ExtractionResult",
    "ExtractedPerson",
    "ExtractedEmployment",
    "ExtractedEducation",
    "ExtractedSkill",
    "ExtractedTechnology",
    "ExtractedCertification",
    "ExtractedProject",
    "ExtractedAchievement",
]
