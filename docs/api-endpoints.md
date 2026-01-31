# API Endpoints

Complete API reference for the AI Semantic Search API.

**Base URL:** `https://e78bx2zpd7.execute-api.us-east-1.amazonaws.com/dev`

---

## Health Check

### `GET /health/`

Check if the API is running.

**Response:**
```json
{
  "status": "ok"
}
```

---

## Documents

### `POST /documents/`

Ingest a document via JSON.

**Request Body:**
```json
{
  "title": "My Document",
  "content": "Document text content here..."
}
```

**Response:**
```json
{
  "document_id": "uuid",
  "title": "My Document",
  "content": "Document text...",
  "created_at": "2026-01-31T12:00:00Z"
}
```

---

### `POST /documents/upload`

Upload a document file (PDF, DOCX, TXT).

**Request:**
- Content-Type: `multipart/form-data`
- Field: `file` (binary file)

**Example:**
```bash
curl -X POST https://your-api.com/dev/documents/upload \
  -F "file=@document.txt"
```

**Response:**
```json
{
  "document_id": "uuid",
  "title": "document.txt",
  "content": "Extracted text...",
  "created_at": "2026-01-31T12:00:00Z"
}
```

**Supported Formats:**
- `.txt` - Plain text
- `.pdf` - PDF documents (text-based)
- `.docx` - Microsoft Word documents

---

### `GET /documents/{document_id}`

Retrieve a specific document by ID.

**Response:**
```json
{
  "document_id": "uuid",
  "title": "My Document",
  "content": "Document text...",
  "created_at": "2026-01-31T12:00:00Z"
}
```

---

### `DELETE /documents/{document_id}`

Delete a document and all its chunks.

**Response:**
```json
{
  "message": "Document deleted successfully",
  "document_id": "uuid"
}
```

---

## Search

### `POST /search/`

Perform semantic search across all documents.

**Request Body:**
```json
{
  "query": "What is machine learning?",
  "top_k": 5
}
```

**Response:**
```json
{
  "query": "What is machine learning?",
  "results": [
    {
      "chunk_id": "uuid",
      "document_id": "uuid",
      "document_title": "AI Guide",
      "content": "Machine learning is...",
      "score": 0.85,
      "index": 0
    }
  ],
  "total_results": 5
}
```

---

## Chat (RAG with LLM)

### `POST /chat/`

Ask questions and get AI-generated answers based on your documents.

**Request Body:**
```json
{
  "query": "What is Python used for in AI?",
  "conversation_id": null,
  "top_k": 5
}
```

**Parameters:**
- `query` (required): Your question
- `conversation_id` (optional): Continue existing conversation (null for new)
- `top_k` (optional): Number of relevant chunks to retrieve (default: 5)

**Response:**
```json
{
  "conversation_id": "uuid",
  "message_id": "uuid",
  "query": "What is Python used for in AI?",
  "answer": "Python is widely used in AI for several reasons...",
  "sources": [
    {
      "document_id": "uuid",
      "document_title": "Python AI Guide",
      "content": "Python has emerged as...",
      "score": 0.92
    }
  ],
  "created_at": "2026-01-31T12:00:00Z"
}
```

**Example - Start Conversation:**
```bash
curl -X POST https://your-api.com/dev/chat/ \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is Python used for in AI?",
    "conversation_id": null
  }'
```

**Example - Continue Conversation:**
```bash
curl -X POST https://your-api.com/dev/chat/ \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Tell me more about that",
    "conversation_id": "uuid-from-previous-response"
  }'
```

---

### `GET /chat/conversations/{conversation_id}`

Retrieve conversation history.

**Response:**
```json
{
  "conversation_id": "uuid",
  "messages": [
    {
      "message_id": "uuid",
      "role": "user",
      "content": "What is Python used for in AI?",
      "created_at": "2026-01-31T12:00:00Z"
    },
    {
      "message_id": "uuid",
      "role": "assistant",
      "content": "Python is widely used...",
      "sources": [...],
      "created_at": "2026-01-31T12:00:01Z"
    }
  ],
  "created_at": "2026-01-31T12:00:00Z",
  "updated_at": "2026-01-31T12:00:01Z"
}
```

---

## Interactive Documentation

**Swagger UI:** `https://your-api.com/dev/docs`
**ReDoc:** `https://your-api.com/dev/redoc`
**OpenAPI JSON:** `https://your-api.com/dev/openapi.json`

---

## Error Responses

All endpoints return consistent error format:

```json
{
  "error": {
    "type": "ErrorType",
    "message": "Human-readable error message",
    "details": {
      "additional": "context"
    }
  }
}
```

**Common Error Types:**
- `DocumentNotFoundException` - Document not found
- `InvalidFileTypeException` - Unsupported file format
- `FileSizeExceededException` - File too large
- `FileProcessingException` - Error processing file
- `EmptyDocumentException` - Document has no content
- `DatabaseException` - Database error
- `VectorStoreException` - Vector store error
- `EmbeddingException` - Embedding generation error
- `InvalidSearchQueryException` - Invalid search query
- `ServiceUnavailableException` - Service temporarily unavailable

---

## Rate Limits

**API Gateway Limits:**
- 100 requests/second (steady state)
- 200 requests/second (burst)

**Lambda Limits:**
- 5-minute timeout per request
- 3 GB memory

---

## Authentication

**Current:** No authentication (public API)

**Production Recommendations:**
- Add API key authentication
- Implement JWT-based auth
- Add per-user rate limiting

---

## Notes

**First Request After Cold Start:**
- May timeout (30 seconds)
- Retry after 5 seconds
- Subsequent requests will be fast

**PDF Limitations:**
- Some PDFs with font issues may fail
- Scanned PDFs not supported (no OCR)
- Workaround: Convert to TXT or DOCX

**Conversation History:**
- Stored in DynamoDB
- Persists across sessions
- No automatic expiration (manual cleanup needed)

---

## Testing Tips

**1. Upload a document first:**
```bash
curl -X POST https://your-api.com/dev/documents/upload \
  -F "file=@test.txt"
```

**2. Search for content:**
```bash
curl -X POST https://your-api.com/dev/chat/ \
  -H "Content-Type: application/json" \
  -d '{"query": "your question here"}'
```

**3. Check conversation history:**
```bash
curl https://your-api.com/dev/chat/conversations/{conversation_id}
```
