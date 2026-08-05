"""Unit tests for orion_kernel.document_intelligence.text_extraction."""
from pathlib import Path

import pytest

from orion_kernel.document_intelligence.text_extraction import TextExtractionError, extract_text

FIXTURES = Path(__file__).parent / "fixtures"


class TestExtractText:
    def test_pdf_extracts_real_text(self):
        content = (FIXTURES / "sample_cv.pdf").read_bytes()
        text = extract_text("pdf", content)
        assert "Ada Lovelace" in text
        assert "Software Engineer" in text

    def test_docx_extracts_real_text(self):
        content = (FIXTURES / "sample_cv.docx").read_bytes()
        text = extract_text("docx", content)
        assert "Ada Lovelace" in text
        assert "Software Engineer" in text

    def test_corrupt_pdf_raises_text_extraction_error(self):
        content = (FIXTURES / "corrupt.pdf").read_bytes()
        with pytest.raises(TextExtractionError):
            extract_text("pdf", content)

    def test_corrupt_docx_raises_text_extraction_error(self):
        content = (FIXTURES / "corrupt.docx").read_bytes()
        with pytest.raises(TextExtractionError):
            extract_text("docx", content)

    def test_unknown_document_type_raises_value_error(self):
        with pytest.raises(ValueError, match="No text extractor"):
            extract_text("txt", b"some content")
