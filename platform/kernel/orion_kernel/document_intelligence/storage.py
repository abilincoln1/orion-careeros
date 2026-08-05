"""
Document storage layer.

Phase 1 of Sprint 3 Stage 1 (Chief Architect Approval v1.0): the
persistence layer, with no extraction logic. `StorageAdapter` is the
interface; `LocalStorageAdapter` is the only implementation authorized
for Stage 1 (a Platform-level shared File Storage capability was
explicitly deferred -- ADR 0005 Decision 1). Migrating to a shared
capability later is an adapter swap, not a rewrite of any caller.
"""
from __future__ import annotations

import hashlib
import os
import re
import secrets
import uuid
from pathlib import Path
from typing import Protocol


class StorageValidationError(ValueError):
    """Raised for any file that fails validation before it is ever
    written to storage -- extension, MIME sniff, or size. Callers (the
    API layer) are expected to catch this and return 422, not let it
    propagate as an unhandled 500."""


class StorageAdapter(Protocol):
    async def store(self, person_id: uuid.UUID, filename: str, content: bytes) -> str:
        """Validates and persists `content`, returning an opaque
        storage_ref meaningful only to this adapter. Raises
        StorageValidationError if the file fails validation (empty,
        oversized, wrong type, or content that doesn't match its
        claimed type)."""
        ...

    async def retrieve(self, storage_ref: str) -> bytes:
        """Raises FileNotFoundError if storage_ref doesn't resolve to
        an existing object."""
        ...

    async def delete(self, storage_ref: str) -> None:
        """Idempotent -- deleting an already-absent storage_ref is not
        an error, consistent with this project's general DELETE
        semantics (see the Career DNA API's 204-on-missing pattern
        where applicable)."""
        ...


# --- Validation constants -----------------------------------------------

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB -- generous for a CV, bounded against abuse

_ALLOWED_EXTENSIONS = {".pdf", ".docx"}

# Magic-byte signatures, checked against actual file content -- never
# trust a client-supplied filename extension or Content-Type header
# alone. No new dependency (e.g. python-magic) was added for this
# minimal signature check; if a broader MIME-sniffing need arises later,
# that's a deliberate follow-up, not silently deferred without a debt
# entry (see docs/TechnicalDebt.md).
_PDF_MAGIC = b"%PDF-"
_DOCX_MAGIC = b"PK\x03\x04"  # DOCX is a zip archive; this is the zip local-file-header signature

_MIME_BY_EXTENSION = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def validate_upload(filename: str, content: bytes) -> str:
    """
    Runs every Phase 1 validation requirement (file validation, MIME
    validation, file size validation) and returns the resolved MIME
    type on success. Raises StorageValidationError with a specific,
    actionable message on any failure -- never a generic "invalid file."
    """
    if not content:
        raise StorageValidationError("Uploaded file is empty.")

    if len(content) > MAX_UPLOAD_BYTES:
        raise StorageValidationError(
            f"File exceeds the {MAX_UPLOAD_BYTES // (1024 * 1024)}MB upload limit."
        )

    extension = Path(filename).suffix.lower()
    if extension not in _ALLOWED_EXTENSIONS:
        raise StorageValidationError(
            f"Unsupported file type '{extension or '(none)'}'. "
            f"Stage 1 supports: {', '.join(sorted(_ALLOWED_EXTENSIONS))}."
        )

    if extension == ".pdf" and not content.startswith(_PDF_MAGIC):
        raise StorageValidationError(
            "File has a .pdf extension but its content does not match a PDF "
            "file signature -- refusing to store a mismatched/corrupt upload."
        )
    if extension == ".docx" and not content.startswith(_DOCX_MAGIC):
        raise StorageValidationError(
            "File has a .docx extension but its content does not match a "
            "DOCX (zip) file signature -- refusing to store a mismatched/"
            "corrupt upload."
        )

    return _MIME_BY_EXTENSION[extension]


def _secure_storage_ref(person_id: uuid.UUID, extension: str) -> str:
    """
    Generates a storage_ref that is (a) scoped by person_id, so no
    directory-listing or enumeration reveals another person's documents,
    and (b) not derived from the client-supplied filename at all -- the
    original filename is preserved only as Document.original_filename
    metadata, never used to construct a filesystem path. This is the
    "secure document path generation" / "secure file naming"
    requirement: an attacker-supplied filename like
    "../../../etc/passwd.pdf" can influence Document.original_filename
    (a plain string column) but never the actual path written to disk.
    """
    random_component = secrets.token_hex(16)
    # person_id is a UUID, already safe as a path segment; re-validated
    # here defensively rather than trusted implicitly from the caller.
    safe_person_id = str(uuid.UUID(str(person_id)))
    return f"{safe_person_id}/{random_component}{extension}"


class LocalStorageAdapter:
    """
    Stage 1's only StorageAdapter implementation: the local filesystem,
    rooted at `base_path`. Not exposed to the network directly -- files
    are only ever read back through `retrieve()`, never served as
    static files, so `base_path` does not need to be web-accessible.
    """

    def __init__(self, base_path: str | os.PathLike):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _resolve(self, storage_ref: str) -> Path:
        """
        Resolves storage_ref to an absolute path, and defensively
        confirms the result is actually inside base_path -- guards
        against a storage_ref that somehow contains '..' segments
        (should be impossible given _secure_storage_ref's construction,
        but this is the last line of defense against path traversal,
        not the only one).
        """
        candidate = (self.base_path / storage_ref).resolve()
        if not str(candidate).startswith(str(self.base_path.resolve())):
            raise StorageValidationError("Invalid storage reference.")
        return candidate

    async def store(self, person_id: uuid.UUID, filename: str, content: bytes) -> str:
        mime_type = validate_upload(filename, content)
        extension = Path(filename).suffix.lower()
        storage_ref = _secure_storage_ref(person_id, extension)
        target = self._resolve(storage_ref)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        return storage_ref

    async def retrieve(self, storage_ref: str) -> bytes:
        target = self._resolve(storage_ref)
        if not target.is_file():
            raise FileNotFoundError(f"No stored document at '{storage_ref}'.")
        return target.read_bytes()

    async def delete(self, storage_ref: str) -> None:
        target = self._resolve(storage_ref)
        target.unlink(missing_ok=True)


def content_checksum(content: bytes) -> str:
    """
    SHA-256 of the raw bytes. Used by DocumentVersion to detect an
    unchanged re-upload (per the Chief Architect's roadmap note on
    avoiding reprocessing unchanged documents) -- comparing checksums is
    how a future version-creation path decides whether a new upload is
    actually a new version or a no-op resubmission of the same file.
    Exposed here (not computed ad hoc at call sites) so the algorithm is
    defined once.
    """
    return hashlib.sha256(content).hexdigest()
