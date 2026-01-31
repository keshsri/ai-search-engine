# Error Handling

## Overview

Comprehensive error handling with custom exceptions, HTTP status mapping, and consistent error responses.

## Exception Hierarchy

All custom exceptions inherit from `SearchAPIException`:

| Exception | HTTP Status | Use Case |
|-----------|-------------|----------|
| `DocumentNotFoundException` | 404 | Document not found |
| `InvalidFileTypeException` | 400 | Unsupported file format |
| `FileSizeExceededException` | 413 | File exceeds 10MB |
| `FileProcessingException` | 422 | Text extraction failed |
| `EmptyDocumentException` | 400 | No extractable content |
| `DatabaseException` | 503 | DynamoDB error |
| `VectorStoreException` | 503 | FAISS error |
| `EmbeddingException` | 503 | Embedding generation failed |
| `InvalidSearchQueryException` | 400 | Invalid query parameters |
| `ServiceUnavailableException` | 503 | External service unavailable |

## Error Response Format

```json
{
  "error": {
    "type": "ErrorType",
    "message": "Human-readable error message",
    "details": {
      "key": "value"
    }
  }
}
```

## Examples

### Document Not Found
```json
{
  "error": {
    "type": "DocumentNotFound",
    "message": "Document not found",
    "details": {
      "document_id": "abc-123"
    }
  }
}
```

### Invalid File Type
```json
{
  "error": {
    "type": "InvalidFileType",
    "message": "Unsupported file type: exe",
    "details": {
      "file_type": "exe",
      "supported_types": ["pdf", "docx", "txt"]
    }
  }
}
```

### File Size Exceeded
```json
{
  "error": {
    "type": "FileSizeExceeded",
    "message": "File size exceeds maximum allowed size",
    "details": {
      "file_size_mb": 15.0,
      "max_size_mb": 10
    }
  }
}
```

### Database Error
```json
{
  "error": {
    "type": "DatabaseError",
    "message": "Database operation failed",
    "details": {
      "error": "ProvisionedThroughputExceededException"
    }
  }
}
```

## Implementation

### Exception Handlers
- Registered in `app/main.py` using `app.add_exception_handler()`
- Specific handlers for each exception type
- Generic handler for unexpected errors
- FastAPI validation errors handled separately

### Service Layer
- Services raise custom exceptions
- AWS boto3 errors caught and wrapped
- Detailed context included in exception details

### Logging
- All errors logged with appropriate levels
- Exception details included in logs
- Stack traces captured for unexpected errors

## Testing

```bash
# Invalid file type
curl -X POST "http://localhost:8000/documents/upload" \
  -F "file=@test.exe"

# File too large
dd if=/dev/zero of=large.txt bs=1M count=15
curl -X POST "http://localhost:8000/documents/upload" \
  -F "file=@large.txt"

# Empty query
curl -X POST "http://localhost:8000/search/" \
  -H "Content-Type: application/json" \
  -d '{"query": "", "top_k": 5}'

# Document not found
curl -X GET "http://localhost:8000/documents/nonexistent-id"
```

## Benefits

1. **Consistent API**: All errors follow same format
2. **Better Debugging**: Detailed context in logs and responses
3. **Type Safety**: Custom exceptions more semantic than generic errors
4. **Separation of Concerns**: Business logic independent of HTTP
5. **Testability**: Easy to test exception handling
