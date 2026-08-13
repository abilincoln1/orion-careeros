"""
Unit tests for DeterministicCVProvider's parsing logic. Uses only
synthetic, invented text -- never the real candidate CV, per the
explicit "do not commit the CV" instruction. See
tests/test_document_intelligence_api.py for the real-CV demonstration,
which is run once, ad hoc, against the actual uploaded files and never
stored as a fixture.
"""
import pytest

from orion_kernel.document_intelligence.deterministic_cv_provider import (
    DeterministicCVProvider,
    parse_employments,
    parse_person_name,
    parse_skills,
)

_SYNTHETIC_CV = """Jane Example
Anytown, UK | (44) 7000000000 | jane.example@example.com

Professional Summary
A fictional systems engineer for testing purposes only.

Key Skills
SCCM, Microsoft Azure, PowerShell, Active Directory, VMware

Professional Experience
Senior Systems Engineer
Acme Testing Ltd | Jan 2021 - Present
- Did fictional work for testing.
- More fictional bullet points.

Systems Administrator
Example Corp, Sometown | Mar 2018 - Dec 2020
- Earlier fictional role.

Education
BSc Computer Science (Fictional) | Fictional University
"""


class TestParseEmployments:
    def test_extracts_current_role_with_present(self):
        results = parse_employments(_SYNTHETIC_CV)
        current = next(r for r in results if r.is_current.value)
        assert current.employer_name.value == "Acme Testing Ltd"
        assert current.role_title.value == "Senior Systems Engineer"
        assert current.start_date.value.isoformat() == "2021-01-01"
        assert current.end_date is None

    def test_extracts_past_role_with_end_date_and_location(self):
        results = parse_employments(_SYNTHETIC_CV)
        past = next(r for r in results if not r.is_current.value)
        assert past.employer_name.value == "Example Corp"  # location stripped
        assert past.role_title.value == "Systems Administrator"
        assert past.start_date.value.isoformat() == "2018-03-01"
        assert past.end_date.value.isoformat() == "2020-12-01"

    def test_extracts_exactly_two_roles_not_more(self):
        results = parse_employments(_SYNTHETIC_CV)
        assert len(results) == 2

    def test_no_employment_lines_produces_empty_list_not_invented_data(self):
        results = parse_employments("Just some random text with no structure at all.")
        assert results == []

    def test_malformed_date_line_is_skipped_not_guessed(self):
        text = "Some Role\nAcme Corp | not-a-real-date - also-not-real\n"
        results = parse_employments(text)
        assert results == []

    def test_employer_date_line_without_preceding_role_title_is_skipped(self):
        text = "Professional Experience\nAcme Corp | Jan 2020 - Present\n"
        results = parse_employments(text)
        assert results == []  # role title line is a section header, not a real title

    def test_bare_year_dates_supported(self):
        text = "Some Role\nAcme Corp | 2015 - 2016\n"
        results = parse_employments(text)
        assert len(results) == 1
        assert results[0].start_date.value.isoformat() == "2015-01-01"
        assert results[0].end_date.value.isoformat() == "2016-01-01"

    def test_duplicate_identical_lines_deduplicated(self):
        """PDF extraction sometimes repeats a line across a page break --
        must not produce two identical Employment extractions."""
        text = "Some Role\nAcme Corp | Jan 2020 - Present\n" * 2
        results = parse_employments(text)
        assert len(results) == 1


class TestParseSkills:
    def test_extracts_known_skills_present_in_text(self):
        results = parse_skills(_SYNTHETIC_CV)
        names = {s.skill_name.value for s in results}
        assert names == {"SCCM", "Microsoft Azure", "PowerShell", "Active Directory", "VMware"}

    def test_does_not_double_count_azure_and_microsoft_azure(self):
        text = "Skilled in Microsoft Azure and general Azure administration."
        results = parse_skills(text)
        names = [s.skill_name.value for s in results]
        assert names.count("Microsoft Azure") + names.count("Azure") == 1

    def test_no_known_skills_produces_empty_list(self):
        results = parse_skills("This text mentions nothing from the known skill list.")
        assert results == []

    def test_case_insensitive_matching(self):
        results = parse_skills("Experience with sccm and powershell.")
        names = {s.skill_name.value for s in results}
        assert "SCCM" in names
        assert "PowerShell" in names


class TestParsePersonName:
    def test_extracts_first_and_last_name_from_first_line(self):
        person = parse_person_name(_SYNTHETIC_CV)
        assert person.first_name.value == "Jane"
        assert person.last_name.value == "Example"

    def test_single_word_first_line_returns_none(self):
        person = parse_person_name("SingleWord\nSecond line here")
        assert person is None

    def test_empty_text_returns_none(self):
        person = parse_person_name("")
        assert person is None


class TestDeterministicCVProvider:
    @pytest.mark.asyncio
    async def test_analyze_returns_populated_result_for_structured_cv(self):
        provider = DeterministicCVProvider()
        result = await provider.analyze("docx", _SYNTHETIC_CV)
        assert len(result.employments) == 2
        assert len(result.skills) == 5
        assert result.persons[0].first_name.value == "Jane"
        assert result.overall_confidence == 0.85

    @pytest.mark.asyncio
    async def test_analyze_low_confidence_when_no_employment_found(self):
        provider = DeterministicCVProvider()
        result = await provider.analyze("docx", "Unstructured text with no CV shape at all.")
        assert result.employments == []
        assert result.overall_confidence == 0.3

    @pytest.mark.asyncio
    async def test_health_check_always_true(self):
        provider = DeterministicCVProvider()
        assert await provider.health_check() is True

    def test_provider_name(self):
        assert DeterministicCVProvider.provider_name == "deterministic-cv-parser"
