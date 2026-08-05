"""
Provider abstraction for document extraction. Phase 4 of Sprint 3
Stage 1. No production AI provider is implemented against this
interface yet -- per the Chief Architect's explicit AI Provider Policy,
that is a later, separately-authorized milestone. This module defines
only the contract; see mock_provider.py for the "complete testing
surface" implementation Stage 1 actually uses.
"""
from __future__ import annotations

from typing import Protocol

from orion_kernel.document_intelligence.extraction_model import ExtractionResult


class ProviderFetchError(RuntimeError):
    """Raised when a provider fails to analyze a document -- a network
    failure, a malformed response, or the provider explicitly
    signalling it could not process the input. Callers (the extraction
    pipeline) are expected to catch this and record the failure on
    DocumentExtractionRun.status, not let it propagate as an unhandled
    500."""


class DocumentExtractionProvider(Protocol):
    provider_name: str

    async def analyze(self, document_type: str, extracted_text: str) -> ExtractionResult:
        """
        Takes already-extracted plain text (converting a PDF/DOCX
        binary into text is the engine's own responsibility, upstream
        of any provider -- see text_extraction.py) and returns a
        structured ExtractionResult. `document_type` is a plain string
        (e.g. "pdf", "docx") rather than a product-specific enum, for
        the same product-agnosticism reason documented in
        extraction_model.py.
        """
        ...

    async def health_check(self) -> bool:
        """Used by an operational dashboard to show whether this
        provider is currently reachable, independent of the last
        successful extraction time."""
        ...
