"""
Text extraction: converts a PDF or DOCX binary into plain text, upstream
of any DocumentExtractionProvider (providers never see raw file bytes --
see provider.py). This is the one place format-specific parsing
libraries (pypdf, python-docx) are imported anywhere in this codebase.
"""
from __future__ import annotations

import io

from orion_kernel.document_intelligence.provider import ProviderFetchError


class TextExtractionError(ProviderFetchError):
    """Raised when a file matches its claimed type's magic bytes (so
    StorageAdapter accepted it) but its internal structure is still
    unreadable -- e.g. a PDF with a valid header but corrupted internal
    xref table. Distinct from StorageValidationError, which catches
    wrong-type/oversized files before they're ever stored."""


def extract_text(document_type: str, content: bytes) -> str:
    if document_type == "pdf":
        return _extract_pdf_text(content)
    if document_type == "docx":
        return _extract_docx_text(content)
    raise ValueError(f"No text extractor registered for document_type={document_type!r}")


def _extract_pdf_text(content: bytes) -> str:
    from pypdf import PdfReader
    from pypdf.errors import PdfReadError

    try:
        reader = PdfReader(io.BytesIO(content))
        pages = [page.extract_text() or "" for page in reader.pages]
    except PdfReadError as exc:
        raise TextExtractionError(f"Could not parse PDF structure: {exc}") from exc

    text = "\n".join(pages).strip()
    if not text:
        raise TextExtractionError(
            "PDF parsed successfully but contains no extractable text -- "
            "likely a scanned/image-only PDF. OCR is out of Stage 1 scope "
            "(see docs/DOCUMENT-INTELLIGENCE-ARCHITECTURE.md Section 9)."
        )
    return text


def _extract_docx_text(content: bytes) -> str:
    import zipfile

    import docx
    from docx.opc.exceptions import PackageNotFoundError

    try:
        document = docx.Document(io.BytesIO(content))
    except (PackageNotFoundError, zipfile.BadZipFile) as exc:
        # BadZipFile: the content isn't even a valid zip archive (DOCX's
        # container format) at all. PackageNotFoundError: it IS a valid
        # zip but missing the OPC parts a DOCX requires. Both are "not a
        # readable DOCX," found via a real corrupt-file test -- a
        # docstring claim of "handles corrupt DOCX" without this second
        # exception type would have been false.
        raise TextExtractionError(f"Could not parse DOCX structure: {exc}") from exc

    paragraphs = [p.text for p in document.paragraphs if p.text.strip()]
    text = "\n".join(paragraphs).strip()
    if not text:
        raise TextExtractionError("DOCX parsed successfully but contains no extractable text.")
    return text
