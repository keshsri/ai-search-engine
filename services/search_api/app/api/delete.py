"""
Delete endpoint for removing documents and their associated data.
"""
import logging
from fastapi import APIRouter, HTTPException, Depends

from app.models.document import DeleteDocumentRequest, DeleteDocumentResponse
from app.services.document_service import DocumentService
from app.dependencies import get_vector_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])


@router.delete("/{document_id}", response_model=DeleteDocumentResponse)
def delete_document(
    document_id: str,
    vector_store=Depends(get_vector_store)
):
    """
    Delete a document and all associated data.
    
    Deletes:
    - Document metadata from DynamoDB
    - All chunks from DynamoDB
    - Vectors from FAISS index
    - Raw file from S3
    
    Args:
        document_id: Document ID to delete
    
    Returns:
        DeleteDocumentResponse with deletion status
    """
    logger.info(f"Delete request for document_id={document_id}")
    
    try:
        # Initialize document service
        document_service = DocumentService(vector_store)
        
        # Delete document and all associated data
        success = document_service.delete(document_id)
        
        if success:
            logger.info(f"Successfully deleted document: {document_id}")
            return DeleteDocumentResponse(
                document_id=document_id,
                deleted=True,
                message="Document and all associated data deleted successfully"
            )
        else:
            logger.warning(f"Document not found: {document_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Document not found: {document_id}"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete document {document_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete document: {str(e)}"
        )
