from fastapi import APIRouter
from app.models.document import Document
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["documents"])

document_service = DocumentService()

@router.post("/", response_model=Document)
def ingest_document(document: Document):
    return document_service.ingest(document)