"""
FastAPI exception handlers for custom exceptions.
Maps domain exceptions to HTTP responses with appropriate status codes.
"""

import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.core.exceptions import (
    SearchAPIException,
    DocumentNotFoundException,
    InvalidFileTypeException,
    FileSizeExceededException,
    FileProcessingException,
    EmptyDocumentException,
    DatabaseException,
    VectorStoreException,
    EmbeddingException,
    InvalidSearchQueryException,
    ServiceUnavailableException,
)

logger = logging.getLogger(__name__)


def create_error_response(
    status_code: int,
    error_type: str,
    message: str,
    details: dict = None
) -> JSONResponse:
    """Create a standardized error response"""
    content = {
        "error": {
            "type": error_type,
            "message": message,
        }
    }
    if details:
        content["error"]["details"] = details
    
    return JSONResponse(
        status_code=status_code,
        content=content
    )


async def document_not_found_handler(request: Request, exc: DocumentNotFoundException) -> JSONResponse:
    logger.warning(f"Document not found: {exc.message}")
    return create_error_response(
        status_code=status.HTTP_404_NOT_FOUND,
        error_type="DocumentNotFound",
        message=exc.message,
        details=exc.details
    )


async def invalid_file_type_handler(request: Request, exc: InvalidFileTypeException) -> JSONResponse:
    logger.warning(f"Invalid file type: {exc.message}")
    return create_error_response(
        status_code=status.HTTP_400_BAD_REQUEST,
        error_type="InvalidFileType",
        message=exc.message,
        details=exc.details
    )


async def file_size_exceeded_handler(request: Request, exc: FileSizeExceededException) -> JSONResponse:
    logger.warning(f"File size exceeded: {exc.message}")
    return create_error_response(
        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        error_type="FileSizeExceeded",
        message=exc.message,
        details=exc.details
    )


async def file_processing_handler(request: Request, exc: FileProcessingException) -> JSONResponse:
    logger.error(f"File processing error: {exc.message}")
    return create_error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        error_type="FileProcessingError",
        message=exc.message,
        details=exc.details
    )


async def empty_document_handler(request: Request, exc: EmptyDocumentException) -> JSONResponse:
    logger.warning(f"Empty document: {exc.message}")
    return create_error_response(
        status_code=status.HTTP_400_BAD_REQUEST,
        error_type="EmptyDocument",
        message=exc.message,
        details=exc.details
    )


async def database_exception_handler(request: Request, exc: DatabaseException) -> JSONResponse:
    logger.error(f"Database error: {exc.message}", exc_info=True)
    return create_error_response(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        error_type="DatabaseError",
        message="Database operation failed. Please try again later.",
        details=exc.details
    )


async def vector_store_exception_handler(request: Request, exc: VectorStoreException) -> JSONResponse:
    logger.error(f"Vector store error: {exc.message}", exc_info=True)
    return create_error_response(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        error_type="VectorStoreError",
        message="Vector store operation failed. Please try again later.",
        details=exc.details
    )


async def embedding_exception_handler(request: Request, exc: EmbeddingException) -> JSONResponse:
    logger.error(f"Embedding error: {exc.message}", exc_info=True)
    return create_error_response(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        error_type="EmbeddingError",
        message="Embedding generation failed. Please try again later.",
        details=exc.details
    )


async def invalid_search_query_handler(request: Request, exc: InvalidSearchQueryException) -> JSONResponse:
    logger.warning(f"Invalid search query: {exc.message}")
    return create_error_response(
        status_code=status.HTTP_400_BAD_REQUEST,
        error_type="InvalidSearchQuery",
        message=exc.message,
        details=exc.details
    )


async def service_unavailable_handler(request: Request, exc: ServiceUnavailableException) -> JSONResponse:
    logger.error(f"Service unavailable: {exc.message}", exc_info=True)
    return create_error_response(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        error_type="ServiceUnavailable",
        message=exc.message,
        details=exc.details
    )


async def generic_search_api_exception_handler(request: Request, exc: SearchAPIException) -> JSONResponse:
    """Catch-all handler for any SearchAPIException not caught by specific handlers"""
    logger.error(f"Unhandled SearchAPIException: {exc.message}", exc_info=True)
    return create_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_type="InternalError",
        message="An unexpected error occurred. Please try again later.",
        details=exc.details
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle FastAPI validation errors"""
    logger.warning(f"Validation error: {exc.errors()}")
    return create_error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        error_type="ValidationError",
        message="Request validation failed",
        details={"errors": exc.errors()}
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler for unexpected exceptions"""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return create_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_type="InternalError",
        message="An unexpected error occurred. Please try again later."
    )
