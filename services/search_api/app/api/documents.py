from fastapi import APIRouter, HTTPException, Depends
from app.models.document import Document
from app.services.document_service import DocumentService
from app.dependencies import get_vector_store

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/", response_model=Document)
def ingest_document(
    document: Document,
    vector_store=Depends(get_vector_store)
):
    service = DocumentService(vector_store)
    return service.ingest(document)


@router.get("/{document_id}", response_model=Document)
def get_document(
    document_id: str,
    vector_store=Depends(get_vector_store)
):
    service = DocumentService(vector_store)
    doc = service.get_by_id(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document Not Found")
    return doc
