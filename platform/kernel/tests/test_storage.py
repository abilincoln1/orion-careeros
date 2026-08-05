"""Unit tests for orion_kernel.document_intelligence.storage."""
import uuid
from pathlib import Path

import pytest

from orion_kernel.document_intelligence.storage import (
    LocalStorageAdapter,
    StorageValidationError,
    content_checksum,
    validate_upload,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _pdf_bytes() -> bytes:
    return (FIXTURES / "sample_cv.pdf").read_bytes()


def _docx_bytes() -> bytes:
    return (FIXTURES / "sample_cv.docx").read_bytes()


class TestValidateUpload:
    def test_valid_pdf_passes(self):
        mime = validate_upload("cv.pdf", _pdf_bytes())
        assert mime == "application/pdf"

    def test_valid_docx_passes(self):
        mime = validate_upload("cv.docx", _docx_bytes())
        assert mime == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    def test_empty_file_rejected(self):
        with pytest.raises(StorageValidationError, match="empty"):
            validate_upload("cv.pdf", b"")

    def test_oversized_file_rejected(self):
        oversized = b"%PDF-" + b"0" * (11 * 1024 * 1024)
        with pytest.raises(StorageValidationError, match="exceeds"):
            validate_upload("cv.pdf", oversized)

    def test_unsupported_extension_rejected(self):
        with pytest.raises(StorageValidationError, match="Unsupported file type"):
            validate_upload("cv.txt", b"plain text content")

    def test_no_extension_rejected(self):
        with pytest.raises(StorageValidationError, match="Unsupported file type"):
            validate_upload("cv", b"some content")

    def test_pdf_extension_with_non_pdf_content_rejected(self):
        """A .pdf extension whose content doesn't match the PDF magic
        bytes must be rejected -- never trust the client-supplied
        extension alone."""
        with pytest.raises(StorageValidationError, match="does not match a PDF"):
            validate_upload("fake.pdf", b"this is not a pdf at all")

    def test_docx_extension_with_non_docx_content_rejected(self):
        with pytest.raises(StorageValidationError, match="does not match a DOCX"):
            validate_upload("fake.docx", b"this is not a docx at all")


class TestLocalStorageAdapter:
    @pytest.fixture
    def adapter(self, tmp_path):
        return LocalStorageAdapter(base_path=tmp_path / "storage")

    @pytest.mark.asyncio
    async def test_store_and_retrieve_round_trip(self, adapter):
        person_id = uuid.uuid4()
        content = _pdf_bytes()
        storage_ref = await adapter.store(person_id, "cv.pdf", content)

        retrieved = await adapter.retrieve(storage_ref)
        assert retrieved == content

    @pytest.mark.asyncio
    async def test_storage_ref_is_person_scoped(self, adapter):
        person_id = uuid.uuid4()
        storage_ref = await adapter.store(person_id, "cv.pdf", _pdf_bytes())
        assert storage_ref.startswith(str(person_id))

    @pytest.mark.asyncio
    async def test_storage_ref_does_not_leak_original_filename(self, adapter):
        """Secure file naming: the original filename must never appear
        in the storage path -- an attacker-supplied filename can only
        ever influence stored *metadata*, never the actual disk path."""
        person_id = uuid.uuid4()
        storage_ref = await adapter.store(
            person_id, "../../../etc/passwd.pdf", _pdf_bytes()
        )
        assert "passwd" not in storage_ref
        assert ".." not in storage_ref

    @pytest.mark.asyncio
    async def test_retrieve_nonexistent_raises(self, adapter):
        with pytest.raises(FileNotFoundError):
            await adapter.retrieve(f"{uuid.uuid4()}/nonexistent.pdf")

    @pytest.mark.asyncio
    async def test_delete_is_idempotent(self, adapter):
        storage_ref = f"{uuid.uuid4()}/nonexistent.pdf"
        await adapter.delete(storage_ref)  # must not raise
        await adapter.delete(storage_ref)  # still must not raise

    @pytest.mark.asyncio
    async def test_store_rejects_invalid_file(self, adapter):
        with pytest.raises(StorageValidationError):
            await adapter.store(uuid.uuid4(), "cv.txt", b"plain text")

    @pytest.mark.asyncio
    async def test_two_uploads_from_same_person_get_different_refs(self, adapter):
        person_id = uuid.uuid4()
        ref1 = await adapter.store(person_id, "cv.pdf", _pdf_bytes())
        ref2 = await adapter.store(person_id, "cv.pdf", _pdf_bytes())
        assert ref1 != ref2  # random component -- never overwrite a prior upload silently


class TestContentChecksum:
    def test_identical_content_same_checksum(self):
        assert content_checksum(b"abc") == content_checksum(b"abc")

    def test_different_content_different_checksum(self):
        assert content_checksum(b"abc") != content_checksum(b"abd")
