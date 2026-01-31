# Error Handling Implementation

## Overview
Comprehensive error handling system with custom exceptions, HTTP status code mapping, and consistent error responses.

## Custom Exceptions

All custom exceptions inherit from `SearchAPIException` and include:
- `message`: Human-readable error description
- `details`: Dictionary with additional context

### Exception Types

| Exception | HTTP Status | Use Case |
|-----------|-------------|----------|
| `DocumentNotFoundException` | 404 | Document not found in database |
| `InvalidFileTypeException` | 400 | Unsupported file format uploaded |
| `FileSizeExceededException` | 413 | File exceeds 10MB limit |
| `FileProcessingException` | 422 | Text extraction failed |
| `EmptyDocumentException` | 400 | No extractable content |
| `DatabaseException` | 503 | DynamoDB operation failed |
| `VectorStoreException` | 503 | FAISS operation failed |
| `EmbeddingException` | 503 | Embedding generation failed |
| `InvalidSearchQueryException` | 400 | Invalid search parameters |
| `ServiceUnavailableException` | 503 | External service unavailable |

## Error Response Format

All errors return a consistent JSON structure:

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
      "supported_types": ["pdf", "docx", "txt"],
      "filename": "malware.exe"
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
      "file_size_bytes": 15728640,
      "max_size_bytes": 10485760,
      "file_size_mb": 15.0,
      "max_size_mb": 10,
      "filename": "large_document.pdf"
    }
  }
}
```

### Database Error
```json
{
  "error": {
    "type": "DatabaseError",
    "message": "Database operation failed. Please try again later.",
    "details": {
      "document_id": "abc-123",
      "error": "ProvisionedThroughputExceededException"
    }
  }
}
```

## Implementation Details

### Exception Handlers
- Registered in `app/main.py` using `app.add_exception_handler()`
- Specific handlers for each exception type
- Generic handlers for unexpected errors
- FastAPI validation errors handled separately

### Service Layer
- Services raise custom exceptions instead of generic errors
- AWS boto3 errors (ClientError, BotoCoreError) caught and wrapped
- Detailed error context included in exception details

### API Layer
- Endpoints validate input and raise appropriate exceptions
- No manual HTTPException raising (handled by exception handlers)
- Clean separation between business logic and HTTP concerns

### Logging
- All errors logged with appropriate levels (WARNING, ERROR)
- Exception details included in logs
- Stack traces captured for unexpected errors

## Benefits

1. **Consistent API**: All errors follow the same response format
2. **Better Debugging**: Detailed error context in logs and responses
3. **Type Safety**: Custom exceptions are more semantic than generic errors
4. **Separation of Concerns**: Business logic doesn't know about HTTP
5. **Testability**: Easy to test exception handling in isolation
6. **User Experience**: Clear, actionable error messages

## Testing Error Handling

### Test Invalid File Type
```bash
curl -X POST "http://localhost:8000/documents/upload" \
  -F "file=@test.exe"
```

### Test File Too Large
```bash
# Create a 15MB file
dd if=/dev/zero of=large.txt bs=1M count=15

curl -X POST "http://localhost:8000/documents/upload" \
  -F "file=@large.txt"
```

### Test Empty Search Query
```bash
curl -X POST "http://localhost:8000/search/" \
  -H "Content-Type: application/json" \
  -d '{"query": "", "top_k": 5}'
```

### Test Document Not Found
```bash
curl -X GET "http://localhost:8000/documents/nonexistent-id"
```

## Future Enhancements

- Retry logic for transient AWS errors
- Circuit breaker pattern for external services
- Rate limiting with custom exceptions
- Request ID tracking across error responses
- Internationalization of error messages
