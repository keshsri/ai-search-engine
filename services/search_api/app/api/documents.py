from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from app.models.document import Document
from app.services.document_service import DocumentService
from app.services.file_processor import FileProcessor
from app.services.file_storage import FileStorage
from app.dependencies import get_vector_store
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])

# Initialize file processing services
file_processor = FileProcessor()
file_storage = FileStorage()


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
    if not doc:
        logger.warning(f"Document not found: id={document_id}")
        raise HTTPException(status_code=404, detail="Document Not Found")
    logger.info(f"Successfully retrieved document: id={document_id}")
    return doc


@router.post("/upload", response_model=Document)
async def upload_document(
    file: UploadFile = File(...),
    vector_store=Depends(get_vector_store)
):
    """
    Upload a document file (PDF, DOCX, or TXT).
    
    Args:
        file: Uploaded file
        vector_store: Injected vector store dependency
    
    Returns:
        Document: Created document with metadata
    
    Raises:
        HTTPException: If file type unsupported or processing fails
    """
    
    logger.info(f"File upload request received: filename='{file.filename}'")
    
    # 1. Validate file type
    file_extension = file.filename.split(".")[-1].lower()
    logger.debug(f"File extension detected: {file_extension}")
    
    if file_extension not in file_processor.SUPPORTED_TYPES:
        logger.error(f"Unsupported file type: {file_extension}")
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file_extension}. Supported: {file_processor.SUPPORTED_TYPES}"
        )
    
    # 2. Validate file size (10MB limit)
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes
    file_content = await file.read()
    file_size = len(file_content)
    
    logger.info(f"File size: {file_size} bytes ({file_size / 1024 / 1024:.2f} MB)")
    
    if file_size > MAX_FILE_SIZE:
        logger.error(f"File too large: {file_size} bytes (max: {MAX_FILE_SIZE})")
        raise HTTPException(
            status_code=400,
            detail=f"File too large: {file_size} bytes. Max: {MAX_FILE_SIZE} bytes (10MB)"
        )
    
    # Reset file pointer after reading
    await file.seek(0)
    
    try:
        # 3. Generate document ID
        document_id = str(uuid.uuid4())
        logger.info(f"Generated document ID: {document_id}")
        
        # 4. Save original file
        logger.debug("Saving original file to storage")
        file_path = file_storage.save(file.file, document_id, file_extension)
        logger.info(f"Original file saved: {file_path}")
        
        # 5. Extract text from file
        await file.seek(0)  # Reset pointer again
        logger.debug("Extracting text from file")
        text = file_processor.extract_text(file.file, file_extension)
        
        if not text or not text.strip():
            logger.error("No text could be extracted from file")
            raise ValueError("No text could be extracted from file")
        
        logger.info(f"Text extracted successfully: {len(text)} characters")
        
        # 6. Create document object
        document = Document(
            id=document_id,
            title=file.filename,  # Use filename as title
            content=text,
            filename=file.filename,
            file_type=file_extension,
            file_size=file_size,
            file_path=file_path
        )
        
        logger.debug(f"Document object created: id={document_id}, title='{document.title}'")
        
        # 7. Ingest document (existing logic)
        logger.info(f"Starting document ingestion: id={document_id}")
        service = DocumentService(vector_store)
        ingested_doc = service.ingest(document)
        
        logger.info(f"Document upload completed successfully: id={document_id}, filename='{file.filename}'")
        
        return ingested_doc
    
    except ValueError as e:
        logger.error(f"Validation error during file upload: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during file upload: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
