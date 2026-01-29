from fastapi import APIRouter, HTTPException
from app.models.document import Document
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["documents"])
service = DocumentService()

@router.post("/", response_model=Document)
def ingest_document(document: Document):
    return service.ingest(document)

@router.get("/{document_id}", response_model=Document)
def get_document(document_id: str):
    doc = service.get_by_id(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document Not Found")
    return doc