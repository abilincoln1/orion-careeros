"""Unit tests for the mock provider and extraction model dataclasses."""
import pytest

from orion_kernel.document_intelligence.extraction_model import ExtractedField, ExtractionResult
from orion_kernel.document_intelligence.mock_provider import MockDocumentExtractionProvider
from orion_kernel.document_intelligence.provider import ProviderFetchError


class TestExtractedField:
    def test_valid_confidence_accepted(self):
        field = ExtractedField(value="Python", confidence=0.9)
        assert field.value == "Python"

    def test_confidence_below_zero_rejected(self):
        with pytest.raises(ValueError, match="confidence must be"):
            ExtractedField(value="x", confidence=-0.1)

    def test_confidence_above_one_rejected(self):
        with pytest.raises(ValueError, match="confidence must be"):
            ExtractedField(value="x", confidence=1.1)


class TestExtractionResult:
    def test_default_empty_result_valid(self):
        result = ExtractionResult()
        assert result.persons == []
        assert result.overall_confidence == 0.0

    def test_invalid_overall_confidence_rejected(self):
        with pytest.raises(ValueError, match="overall_confidence must be"):
            ExtractionResult(overall_confidence=1.5)


class TestMockDocumentExtractionProvider:
    @pytest.mark.asyncio
    async def test_clean_fixture_returns_high_confidence_result(self):
        provider = MockDocumentExtractionProvider(fixture="clean")
        result = await provider.analyze("pdf", "irrelevant text -- fixture-driven")
        assert result.overall_confidence > 0.9
        assert len(result.persons) == 1
        assert result.persons[0].first_name.value == "Ada"
        assert len(result.employments) == 1
        assert len(result.skills) == 2

    @pytest.mark.asyncio
    async def test_low_confidence_fixture(self):
        provider = MockDocumentExtractionProvider(fixture="low_confidence")
        result = await provider.analyze("pdf", "irrelevant")
        assert result.overall_confidence < 0.5

    @pytest.mark.asyncio
    async def test_partial_fixture_has_empty_sections(self):
        provider = MockDocumentExtractionProvider(fixture="partial")
        result = await provider.analyze("pdf", "irrelevant")
        assert len(result.persons) == 1
        assert result.employments == []
        assert result.skills == []

    @pytest.mark.asyncio
    async def test_unhealthy_provider_raises_on_analyze(self):
        provider = MockDocumentExtractionProvider(fixture="clean", healthy=False)
        with pytest.raises(ProviderFetchError):
            await provider.analyze("pdf", "irrelevant")

    @pytest.mark.asyncio
    async def test_health_check_reflects_configured_state(self):
        healthy = MockDocumentExtractionProvider(healthy=True)
        unhealthy = MockDocumentExtractionProvider(healthy=False)
        assert await healthy.health_check() is True
        assert await unhealthy.health_check() is False

    def test_unknown_fixture_rejected_at_construction(self):
        with pytest.raises(ValueError, match="Unknown fixture"):
            MockDocumentExtractionProvider(fixture="does-not-exist")
