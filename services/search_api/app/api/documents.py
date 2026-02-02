from fastapi import APIRouter, Depends, UploadFile, File
from app.models.document import Document
from app.services.document_service import DocumentService
from app.services.file_processor import FileProcessor
from app.services.file_storage import FileStorage
from app.dependencies import get_vector_store
from app.core.exceptions import (
    InvalidFileTypeException,
    FileSizeExceededException,
    EmptyDocumentException,
)
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])

file_processor = FileProcessor()
file_storage = FileStorage()


@router.get("/", response_model=list)
def list_documents(
    vector_store=Depends(get_vector_store)
):
    logger.info("Listing all documents")
    service = DocumentService(vector_store)
    
    try:
        response = service.db.table.scan()
        documents = response.get('Items', [])
        
        result = []
        for doc in documents:
            from datetime import datetime
            created_at = doc.get("created_at", datetime.utcnow().isoformat())
            
            result.append({
                "document_id": doc.get("document_id"),
                "title": doc.get("title", "Untitled"),
                "created_at": created_at,
                "source": doc.get("source")
            })
        
        result.sort(key=lambda x: x['created_at'], reverse=True)
        
        logger.info(f"Found {len(result)} documents")
        return result
    except Exception as e:
        logger.error(f"Failed to list documents: {str(e)}")
        raise


@router.post("/", response_model=Document)
def ingest_document(
    document: Document,
    vector_store=Depends(get_vector_store)
):
    logger.info(f"Ingesting document via JSON: title='{document.title}'")
    service = DocumentService(vector_store)
    result = service.ingest(document)
    logger.info(f"Successfully ingested document: id={result.id}")
    return result


@router.get("/{document_id}", response_model=Document)
def get_document(
    document_id: str,
    vector_store=Depends(get_vector_store)
):
    logger.info(f"Retrieving document: id={document_id}")
    service = DocumentService(vector_store)
    doc = service.get_by_id(document_id)
    logger.info(f"Successfully retrieved document: id={document_id}")
    return doc


@router.post("/upload", response_model=Document)
async def upload_document(
    file: UploadFile = File(...),
    vector_store=Depends(get_vector_store)
):
    logger.info(f"File upload request received: filename='{file.filename}'")
    
    file_extension = file.filename.split(".")[-1].lower()
    logger.debug(f"File extension detected: {file_extension}")
    
    if file_extension not in file_processor.SUPPORTED_TYPES:
        logger.error(f"Unsupported file type: {file_extension}")
        raise InvalidFileTypeException(
            message=f"Unsupported file type: {file_extension}",
            details={
                "file_type": file_extension,
                "supported_types": file_processor.SUPPORTED_TYPES,
                "filename": file.filename
            }
        )
    
    MAX_FILE_SIZE = 10 * 1024 * 1024
    file_content = await file.read()
    file_size = len(file_content)
    
    logger.info(f"File size: {file_size} bytes ({file_size / 1024 / 1024:.2f} MB)")
    
    if file_size > MAX_FILE_SIZE:
        logger.error(f"File too large: {file_size} bytes (max: {MAX_FILE_SIZE})")
        raise FileSizeExceededException(
            message=f"File size exceeds maximum allowed size",
            details={
                "file_size_bytes": file_size,
                "max_size_bytes": MAX_FILE_SIZE,
                "file_size_mb": round(file_size / 1024 / 1024, 2),
                "max_size_mb": 10,
                "filename": file.filename
            }
        )
    
    await file.seek(0)
    
    document_id = str(uuid.uuid4())
    logger.info(f"Generated document ID: {document_id}")
    
    logger.debug("Saving original file to storage")
    file_path = file_storage.save(file.file, document_id, file_extension)
    logger.info(f"Original file saved: {file_path}")
    
    await file.seek(0)
    logger.debug("Extracting text from file")
    text = file_processor.extract_text(file.file, file_extension)
    
    if not text or not text.strip():
        logger.error("No text could be extracted from file")
        raise EmptyDocumentException(
            message="No text could be extracted from file",
            details={"filename": file.filename, "file_type": file_extension}
        )
    
    logger.info(f"Text extracted successfully: {len(text)} characters")
    
    document = Document(
        id=document_id,
        title=file.filename,
        content=text,
        filename=file.filename,
        file_type=file_extension,
        file_size=file_size,
        file_path=file_path
    )
    
    logger.debug(f"Document object created: id={document_id}, title='{document.title}'")
    
    logger.info(f"Starting document ingestion: id={document_id}")
    service = DocumentService(vector_store)
    ingested_doc = service.ingest(document)
    
    logger.info(f"Document upload completed successfully: id={document_id}, filename='{file.filename}'")
    
    return ingested_doc
