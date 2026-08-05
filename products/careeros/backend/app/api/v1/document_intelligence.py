"""Document Intelligence Engine endpoints (Sprint 3 Stage 1)."""
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_person, get_extraction_provider, get_storage_adapter
from app.core.database import get_db
from app.models.document import Document
from app.models.enums import DocumentType
from app.models.person import Person
from app.schemas.document_intelligence import (
    ApplySummary,
    DocumentExtractionRunRead,
    DocumentRead,
)
from app.services import document_intelligence_service

router = APIRouter(prefix="/document-intelligence", tags=["document-intelligence"])

_EXTENSION_TO_TYPE = {".pdf": DocumentType.PDF, ".docx": DocumentType.DOCX}


@router.post("/documents", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    current_person: Person = Depends(get_current_person),
    db: AsyncSession = Depends(get_db),
    storage=Depends(get_storage_adapter),
) -> Document:
    filename = file.filename or ""
    extension = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    document_type = _EXTENSION_TO_TYPE.get(extension)
    if document_type is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported file type '{extension or '(none)'}'. Supported: .pdf, .docx",
        )

    content = await file.read()
    try:
        return await document_intelligence_service.upload_document(
            db, storage, current_person, document_type, filename, content
        )
    except document_intelligence_service.StorageValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


@router.get("/documents", response_model=list[DocumentRead])
async def list_documents(
    current_person: Person = Depends(get_current_person),
    db: AsyncSession = Depends(get_db),
) -> list[Document]:
    return await document_intelligence_service.list_documents(db, current_person)


@router.get("/documents/{document_id}", response_model=DocumentRead)
async def get_document(
    document_id: uuid.UUID,
    current_person: Person = Depends(get_current_person),
    db: AsyncSession = Depends(get_db),
) -> Document:
    return await document_intelligence_service.get_document_or_404(db, current_person, document_id)


@router.post(
    "/documents/{document_id}/extract",
    response_model=DocumentExtractionRunRead,
    status_code=status.HTTP_201_CREATED,
)
async def trigger_extraction(
    document_id: uuid.UUID,
    current_person: Person = Depends(get_current_person),
    db: AsyncSession = Depends(get_db),
    storage=Depends(get_storage_adapter),
    provider=Depends(get_extraction_provider),
):
    document = await document_intelligence_service.get_document_or_404(db, current_person, document_id)
    run = await document_intelligence_service.extract(db, storage, provider, document)
    return _run_with_result(run)


@router.get("/documents/{document_id}/runs/{run_id}", response_model=DocumentExtractionRunRead)
async def get_extraction_run(
    document_id: uuid.UUID,
    run_id: uuid.UUID,
    current_person: Person = Depends(get_current_person),
    db: AsyncSession = Depends(get_db),
):
    document = await document_intelligence_service.get_document_or_404(db, current_person, document_id)
    run = await document_intelligence_service.get_run_or_404(db, document, run_id)
    return _run_with_result(run)


@router.post("/documents/{document_id}/runs/{run_id}/apply", response_model=ApplySummary)
async def apply_extraction_run(
    document_id: uuid.UUID,
    run_id: uuid.UUID,
    current_person: Person = Depends(get_current_person),
    db: AsyncSession = Depends(get_db),
):
    document = await document_intelligence_service.get_document_or_404(db, current_person, document_id)
    run = await document_intelligence_service.get_run_or_404(db, document, run_id)
    return await document_intelligence_service.apply(db, current_person, run)


def _run_with_result(run):
    """Attaches the deserialized extraction_result onto the ORM object
    for response_model serialization -- raw_extraction_json is stored
    as JSON already, DocumentExtractionRunRead just needs it under the
    `extraction_result` field name, not `raw_extraction_json`."""
    run.extraction_result = run.raw_extraction_json
    return run
