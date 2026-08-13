"""
DeterministicCVProvider -- a real, rule-based DocumentExtractionProvider.
No LLM. Directive-driven (MVP "Next Task -- Minimum Real-CV Extraction
Capability", 13 August 2026): the audit confirmed this project's
Document Intelligence pipeline already does real text extraction from
real uploaded files (text_extraction.py, tested, already wired into
extract()) -- the only gap was that the sole provider implementation
(MockDocumentExtractionProvider) ignored that real text and returned
fixture data regardless of input. This provider is the minimum viable
fix: it actually reads the text extract() already produces.

Deliberately narrow, per the directive's explicit "do not build a
general-purpose document intelligence platform" instruction: this
parses the specific, consistent structure both of the candidate's real
CVs share (confirmed by inspecting the actual output of this project's
own extract_text() against both real uploaded files, not assumed):

    Role Title
    Employer Name | Mon YYYY - Mon YYYY
    - bullet line
    - bullet line
    ...

This is NOT a general CV parser -- a differently-formatted CV will
simply extract fewer or no employment records (never invented ones;
see the confidence/None-on-no-match discipline throughout). Skills are
matched against a small, explicit keyword list, not inferred by any
statistical or AI process -- every matched skill is traceable to an
exact substring in the source text.
"""
from __future__ import annotations

import re
from datetime import date

from orion_kernel.document_intelligence.extraction_model import (
    ExtractedEmployment,
    ExtractedField,
    ExtractedPerson,
    ExtractedSkill,
    ExtractionResult,
)

_MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}

# Matches "Employer Name | Mon YYYY - Mon YYYY" (also "- Present", also
# bare "YYYY - YYYY"), tolerating both the ASCII hyphen and en-dash
# characters observed in the two real source documents, and an
# optional ", Location" after the employer name.
_EMPLOYER_DATE_LINE = re.compile(
    r"^(?P<employer>[^|]+?)(?:,\s*[^|]+?)?\s*\|\s*"
    r"(?P<start>[A-Za-z]{3,9}\.?\s+\d{4}|\d{4})\s*[\u2013\u2014-]\s*"
    r"(?P<end>Present|[A-Za-z]{3,9}\.?\s+\d{4}|\d{4})\s*$"
)

_SECTION_HEADER_WORDS = {
    "professional experience", "experience", "employment", "work history",
}

# Deliberately small and explicit -- every entry here is a real skill
# named in the candidate's actual CVs (confirmed by direct reading), not
# a generic industry list. Matched as whole words/phrases, case-insensitive.
_KNOWN_SKILLS = [
    "SCCM", "MECM", "Microsoft Intune", "Intune", "Microsoft Azure", "Azure",
    "AWS", "PowerShell", "Bash", "Python", "Active Directory", "Group Policy",
    "VMware", "Hyper-V", "Windows Server", "App-V", "AdminStudio",
    "InstallShield", "Citrix", "CyberArk", "Google Colab", "Office 365",
    "Microsoft 365",
]


def _parse_date(text: str) -> date | None:
    text = text.strip().rstrip(".")
    if text.lower() == "present":
        return None
    match = re.match(r"([A-Za-z]{3,9})\.?\s+(\d{4})", text)
    if match:
        month_name, year = match.groups()
        month = _MONTHS.get(month_name[:3].lower())
        if month:
            return date(int(year), month, 1)
    match = re.match(r"^(\d{4})$", text)
    if match:
        return date(int(match.group(1)), 1, 1)
    return None


def parse_employments(text: str) -> list[ExtractedEmployment]:
    """
    Real, deterministic parsing -- no invention. A line only becomes an
    ExtractedEmployment if it matches _EMPLOYER_DATE_LINE exactly; the
    role title is only taken from the immediately preceding non-blank
    line, and only if that line is not itself a section header. Dates
    that don't parse are left as None (ExtractedField absent), never
    guessed.
    """
    lines = [ln.strip() for ln in text.splitlines()]
    results: list[ExtractedEmployment] = []
    seen: set[tuple[str, str]] = set()  # (employer, start) -- de-dup identical lines appearing twice (e.g. PDF page-break artefacts)

    for i, line in enumerate(lines):
        match = _EMPLOYER_DATE_LINE.match(line)
        if not match:
            continue

        employer = match.group("employer").strip()
        if not employer or employer.lower() in _SECTION_HEADER_WORDS:
            continue

        role_title = None
        for j in range(i - 1, max(i - 3, -1), -1):
            candidate = lines[j].strip()
            if not candidate:
                continue
            if candidate.lower() in _SECTION_HEADER_WORDS:
                break
            role_title = candidate
            break
        if not role_title:
            continue  # per "do not invent" -- no role title found, skip this block entirely

        start_date = _parse_date(match.group("start"))
        end_raw = match.group("end")
        is_current = end_raw.strip().lower() == "present"
        end_date = None if is_current else _parse_date(end_raw)

        key = (employer.lower(), match.group("start"))
        if key in seen:
            continue
        seen.add(key)

        results.append(
            ExtractedEmployment(
                employer_name=ExtractedField(employer, confidence=1.0),
                role_title=ExtractedField(role_title, confidence=0.9),  # 0.9, not 1.0: positional inference (preceding line), not a labelled field
                is_current=ExtractedField(is_current, confidence=1.0),
                start_date=ExtractedField(start_date, confidence=1.0) if start_date else None,
                end_date=ExtractedField(end_date, confidence=1.0) if end_date else None,
            )
        )
    return results


def parse_skills(text: str) -> list[ExtractedSkill]:
    """Matches _KNOWN_SKILLS as whole words/phrases against the full
    document text. Longer entries (e.g. "Microsoft Intune") are checked
    before their shorter substrings (e.g. "Intune") and, once matched,
    the shorter form is not added again for the same underlying skill --
    avoids double-counting "Azure" both standalone and inside "Microsoft
    Azure" as two different skills."""
    found: dict[str, None] = {}
    remaining_skills = list(_KNOWN_SKILLS)
    for skill in remaining_skills:
        pattern = re.compile(r"\b" + re.escape(skill) + r"\b", re.IGNORECASE)
        if pattern.search(text):
            canonical = skill
            if skill == "Intune" and "Microsoft Intune" in found:
                continue
            if skill == "Azure" and "Microsoft Azure" in found:
                continue
            found[canonical] = None
    return [
        ExtractedSkill(skill_name=ExtractedField(name, confidence=1.0), skill_type=ExtractedField("technical", confidence=1.0))
        for name in found
    ]


def parse_person_name(text: str) -> ExtractedPerson | None:
    """The candidate's name is deterministically the first non-blank
    line of the document, per both real source CVs' actual structure --
    verified, not assumed as a general rule for arbitrary CVs."""
    for line in text.splitlines():
        line = line.strip()
        if line:
            parts = line.split()
            if len(parts) >= 2:
                return ExtractedPerson(
                    first_name=ExtractedField(parts[0], confidence=0.8),
                    last_name=ExtractedField(" ".join(parts[1:]), confidence=0.8),
                )
            return None
    return None


class DeterministicCVProvider:
    """A real DocumentExtractionProvider -- no LLM, no fixture. Reads
    the actual text extract() produces from the actual uploaded file."""

    provider_name = "deterministic-cv-parser"

    async def analyze(self, document_type: str, extracted_text: str) -> ExtractionResult:
        person = parse_person_name(extracted_text)
        employments = parse_employments(extracted_text)
        skills = parse_skills(extracted_text)

        # A simple, honest confidence signal -- not a statistical
        # model: proportional to how much of the document's structure
        # was successfully recognised. Full detail in the completion
        # report; this is not presented anywhere as a calibrated
        # probability.
        overall_confidence = 0.85 if employments else 0.3

        return ExtractionResult(
            persons=[person] if person else [],
            employments=employments,
            skills=skills,
            overall_confidence=overall_confidence,
        )

    async def health_check(self) -> bool:
        return True
