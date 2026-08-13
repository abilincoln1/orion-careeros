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


def _real_cv_demo_result() -> ExtractionResult:
    """
    TD-023 Option B real-CV demonstration fixture (MVP directive
    Section 8-9). This is NOT LLM extraction output -- no LLM provider
    is authorised in this project's current scope (the MVP directive's
    Architecture Freeze explicitly forbids new AI agents). This data
    was manually transcribed directly from the candidate's own primary
    CV documents (Abiodun_Adeniran_update_cv.pdf and Cloud_Support_Cv.docx
    -- reconciled: both sources agree on every employer name and date
    below, confirmed by direct diff), standing in for a provider that
    does not yet exist, per the directive's explicit instruction not to
    fabricate an LLM extraction result. Every value below is
    independently verifiable against the two source documents; nothing
    is invented. Neither CV file is committed to this repository.
    """
    return ExtractionResult(
        persons=[
            ExtractedPerson(
                first_name=ExtractedField("Abiodun", confidence=1.0),
                last_name=ExtractedField("Adeniran", confidence=1.0),
                headline=ExtractedField("Systems Engineer and Cybersecurity Specialist", confidence=0.9),
            )
        ],
        employments=[
            ExtractedEmployment(
                employer_name=ExtractedField("Wm Morrisons Supermarkets Ltd", confidence=1.0),
                role_title=ExtractedField("Technology Analyst - Systems Engineer", confidence=1.0),
                is_current=ExtractedField(True, confidence=1.0),
                start_date=ExtractedField(date(2022, 2, 1), confidence=1.0),
                description=ExtractedField(
                    "Managing enterprise IT infrastructure with SCCM, Intune, and Azure.", confidence=0.9
                ),
                # employment_type intentionally omitted -- neither source
                # document states a contract type for this role; the
                # apply() fallback (full_time) will be used and disclosed.
            ),
            ExtractedEmployment(
                employer_name=ExtractedField("De Montfort University", confidence=1.0),
                role_title=ExtractedField("Applications Packager - Systems Engineer", confidence=1.0),
                is_current=ExtractedField(False, confidence=1.0),
                start_date=ExtractedField(date(2020, 10, 1), confidence=1.0),
                end_date=ExtractedField(date(2022, 5, 31), confidence=1.0),
            ),
            ExtractedEmployment(
                employer_name=ExtractedField("Dell - Johnson Matthey", confidence=1.0),
                role_title=ExtractedField("Applications Discovery & Testing", confidence=1.0),
                is_current=ExtractedField(False, confidence=1.0),
                start_date=ExtractedField(date(2020, 3, 1), confidence=1.0),
                end_date=ExtractedField(date(2020, 10, 1), confidence=1.0),
            ),
            ExtractedEmployment(
                employer_name=ExtractedField("Birmingham City University", confidence=1.0),
                role_title=ExtractedField("Applications Packager", confidence=1.0),
                is_current=ExtractedField(False, confidence=1.0),
                start_date=ExtractedField(date(2016, 3, 1), confidence=1.0),
                end_date=ExtractedField(date(2019, 12, 31), confidence=1.0),
            ),
            ExtractedEmployment(
                employer_name=ExtractedField("Network Rail", confidence=1.0),
                role_title=ExtractedField("Applications Packager", confidence=1.0),
                is_current=ExtractedField(False, confidence=0.8),  # only year, not month, given in source
                start_date=ExtractedField(date(2015, 1, 1), confidence=0.6),
                end_date=ExtractedField(date(2016, 1, 1), confidence=0.6),
            ),
            ExtractedEmployment(
                employer_name=ExtractedField("Health & Safety Executive", confidence=1.0),
                role_title=ExtractedField("Applications Packager", confidence=1.0),
                is_current=ExtractedField(False, confidence=0.8),
                start_date=ExtractedField(date(2012, 1, 1), confidence=0.6),
                end_date=ExtractedField(date(2014, 1, 1), confidence=0.6),
            ),
        ],
        skills=[
            # A representative subset of the CV's "Key Skills" section
            # (both primary sources list these identically), not every
            # tool mentioned -- deliberately small per "smallest thing
            # that produces measurable value," not an exhaustive
            # re-transcription of the whole document.
            ExtractedSkill(skill_name=ExtractedField("SCCM", confidence=1.0), skill_type=ExtractedField("technical", confidence=1.0)),
            ExtractedSkill(skill_name=ExtractedField("Microsoft Intune", confidence=1.0), skill_type=ExtractedField("technical", confidence=1.0)),
            ExtractedSkill(skill_name=ExtractedField("Microsoft Azure", confidence=1.0), skill_type=ExtractedField("technical", confidence=1.0)),
            ExtractedSkill(skill_name=ExtractedField("PowerShell", confidence=1.0), skill_type=ExtractedField("technical", confidence=1.0)),
            ExtractedSkill(skill_name=ExtractedField("Active Directory", confidence=1.0), skill_type=ExtractedField("technical", confidence=1.0)),
            ExtractedSkill(skill_name=ExtractedField("VMware", confidence=1.0), skill_type=ExtractedField("technical", confidence=1.0)),
            # proficiency intentionally omitted for all skills above --
            # neither source CV states a self-assessed proficiency level
            # per skill; the apply() fallback (intermediate) will be
            # used and disclosed, per the directive's explicit
            # instruction not to present an unverified proficiency as
            # a confirmed candidate capability.
        ],
        overall_confidence=0.93,
    )


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
    "real_cv_demo": _real_cv_demo_result,
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
