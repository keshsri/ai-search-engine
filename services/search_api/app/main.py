from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
import os

from app.api import health, documents, search, chat, delete, conversations
from app.core.logging import setup_logging
from app.core.config import settings
from app.core.exceptions import (
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
    SearchAPIException,
)
from app.core.error_handlers import (
    document_not_found_handler,
    invalid_file_type_handler,
    file_size_exceeded_handler,
    file_processing_handler,
    empty_document_handler,
    database_exception_handler,
    vector_store_exception_handler,
    embedding_exception_handler,
    invalid_search_query_handler,
    service_unavailable_handler,
    generic_search_api_exception_handler,
    validation_exception_handler,
    generic_exception_handler,
)

setup_logging()

root_path = ""
if os.environ.get('AWS_LAMBDA_FUNCTION_NAME'):
    root_path = f"/{os.environ.get('API_GATEWAY_STAGE', 'dev')}"

app = FastAPI(
    title=settings.APP_NAME,
    description="Intelligent search engine combining documents and web search with AI-powered answers",
    version="1.0.0",
    root_path=root_path,
)

app.add_exception_handler(DocumentNotFoundException, document_not_found_handler)
app.add_exception_handler(InvalidFileTypeException, invalid_file_type_handler)
app.add_exception_handler(FileSizeExceededException, file_size_exceeded_handler)
app.add_exception_handler(FileProcessingException, file_processing_handler)
app.add_exception_handler(EmptyDocumentException, empty_document_handler)
app.add_exception_handler(DatabaseException, database_exception_handler)
app.add_exception_handler(VectorStoreException, vector_store_exception_handler)
app.add_exception_handler(EmbeddingException, embedding_exception_handler)
app.add_exception_handler(InvalidSearchQueryException, invalid_search_query_handler)
app.add_exception_handler(ServiceUnavailableException, service_unavailable_handler)
app.add_exception_handler(SearchAPIException, generic_search_api_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

app.include_router(health.router)
app.include_router(documents.router)
app.include_router(search.router)
app.include_router(chat.router)
app.include_router(conversations.router)
app.include_router(delete.router)
