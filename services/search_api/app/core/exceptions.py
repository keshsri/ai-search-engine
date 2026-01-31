"""
Custom exception classes for the search API.
These exceptions map to specific HTTP status codes and provide clear error messages.
"""


class SearchAPIException(Exception):
    """Base exception for all search API errors"""
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class DocumentNotFoundException(SearchAPIException):
    """Raised when a document is not found in the database"""
    pass


class InvalidFileTypeException(SearchAPIException):
    """Raised when an unsupported file type is uploaded"""
    pass


class FileSizeExceededException(SearchAPIException):
    """Raised when uploaded file exceeds size limit"""
    pass


class FileProcessingException(SearchAPIException):
    """Raised when file content extraction fails"""
    pass


class EmptyDocumentException(SearchAPIException):
    """Raised when document has no extractable content"""
    pass


class DatabaseException(SearchAPIException):
    """Raised when database operations fail"""
    pass


class VectorStoreException(SearchAPIException):
    """Raised when vector store operations fail"""
    pass


class EmbeddingException(SearchAPIException):
    """Raised when embedding generation fails"""
    pass


class InvalidSearchQueryException(SearchAPIException):
    """Raised when search query is invalid or empty"""
    pass


class ServiceUnavailableException(SearchAPIException):
    """Raised when external services are unavailable"""
    pass
