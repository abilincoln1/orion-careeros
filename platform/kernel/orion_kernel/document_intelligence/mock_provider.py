"""
MockDocumentExtractionProvider -- Stage 1's only provider
implementation, per the Chief Architect's directive: "This provider
becomes the complete testing surface. Every downstream component
should operate against this interface. No production LLM provider
should be introduced until the interface is proven."

Deterministic, fixture-driven, and covers the scenarios
docs/SPRINT-3-STAGE1-TEST-STRATEGY.md specifies: a clean high-confidence
extraction, a low-confidence extraction, a partial extraction (some
fields absent), and a simulated health-check failure -- selected by
which fixture key the caller passes in, not randomness, so tests are
reproducible.
"""
from __future__ import annotations

from datetime import date

from orion_kernel.document_intelligence.extraction_model import (
    ExtractedEmployment,
    ExtractedField,
    ExtractedPerson,
    ExtractedSkill,
    ExtractionResult,
)
from orion_kernel.document_intelligence.provider import ProviderFetchError


def _clean_high_confidence_result() -> ExtractionResult:
    return ExtractionResult(
        persons=[
            ExtractedPerson(
                first_name=ExtractedField("Ada", confidence=0.98),
                last_name=ExtractedField("Lovelace", confidence=0.98),
                headline=ExtractedField("Software Engineer", confidence=0.9),
            )
        ],
        employments=[
            ExtractedEmployment(
                employer_name=ExtractedField("Acme Corp", confidence=0.95),
                role_title=ExtractedField("Software Engineer", confidence=0.95),
                is_current=ExtractedField(True, confidence=0.9),
                start_date=ExtractedField(date(2020, 1, 1), confidence=0.85),
            )
        ],
        skills=[
            ExtractedSkill(skill_name=ExtractedField("Python", confidence=0.97)),
            ExtractedSkill(skill_name=ExtractedField("SQL", confidence=0.92)),
        ],
        overall_confidence=0.94,
    )


def _low_confidence_result() -> ExtractionResult:
    return ExtractionResult(
        persons=[
            ExtractedPerson(
                first_name=ExtractedField("Unclear", confidence=0.4),
                last_name=ExtractedField("Name", confidence=0.35),
            )
        ],
        skills=[ExtractedSkill(skill_name=ExtractedField("Possibly Python", confidence=0.3))],
        overall_confidence=0.35,
    )


def _partial_result() -> ExtractionResult:
    """Only some fields populated -- confirms the pipeline doesn't
    assume every section of a document is always present."""
    return ExtractionResult(
        persons=[ExtractedPerson(first_name=ExtractedField("Partial", confidence=0.8), last_name=ExtractedField("Data", confidence=0.8))],
        overall_confidence=0.8,
    )


_FIXTURES = {
    "clean": _clean_high_confidence_result,
    "low_confidence": _low_confidence_result,
    "partial": _partial_result,
}


class MockDocumentExtractionProvider:
    provider_name = "mock"

    def __init__(self, fixture: str = "clean", healthy: bool = True):
        if fixture not in _FIXTURES:
            raise ValueError(f"Unknown fixture '{fixture}'. Valid: {sorted(_FIXTURES)}")
        self._fixture = fixture
        self._healthy = healthy

    async def analyze(self, document_type: str, extracted_text: str) -> ExtractionResult:
        if not self._healthy:
            raise ProviderFetchError("Mock provider configured as unhealthy for this test.")
        return _FIXTURES[self._fixture]()

    async def health_check(self) -> bool:
        return self._healthy
