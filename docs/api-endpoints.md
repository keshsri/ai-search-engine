# API Reference

Complete API documentation for OmniSearch AI.

## Base URL

```
https://<api-id>.execute-api.<region>.amazonaws.com/dev
```

Replace with your actual API Gateway endpoint after deployment.

## Authentication

No authentication required.

## Endpoints

### Health Check

```http
GET /health/
```

**Response**:
```json
{"status": "ok"}
```

---

### List Documents

```http
GET /documents/
```

**Response**:
```json
[
  {
    "document_id": "uuid",
    "title": "Document Title",
    "created_at": "2026-01-31T12:00:00Z",
    "source": null
  }
]
```

---

### Ingest Document (JSON)

```http
POST /documents/
Content-Type: application/json

{
  "title": "Document Title",
  "content": "Document text content..."
}
```

**Response**:
```json
{
  "id": "uuid",
  "title": "Document Title",
  "content": "Document text...",
  "created_at": "2026-01-31T12:00:00Z"
}
```

---

### Upload Document (File)

```http
POST /documents/upload
Content-Type: multipart/form-data

file: <binary>
```

**Supported formats**: PDF, DOCX, TXT (max 10MB)

**Example**:
```bash
curl -X POST https://your-api/dev/documents/upload \
  -F "file=@document.pdf"
```

**Response**: Same as JSON ingestion

---

### Get Document

```http
GET /documents/{document_id}
```

**Response**:
```json
{
  "id": "uuid",
  "title": "Document Title",
  "content": "Full text...",
  "created_at": "2026-01-31T12:00:00Z"
}
```

---

### Delete Document

```http
DELETE /documents/{document_id}
```

Deletes document and all associated data:
- Document metadata from DynamoDB
- All chunks from DynamoDB
- Vectors from FAISS index
- Raw file from S3

**Response**:
```json
{
  "document_id": "uuid",
  "deleted": true,
  "message": "Document and all associated data deleted successfully"
}
```

---

### Semantic Search

```http
POST /search/
Content-Type: application/json

{
  "query": "What is machine learning?",
  "top_k": 5
}
```

**Parameters**:
- `query` (required): Search query
- `top_k` (optional): Number of results (default: 5, max: 10)

**Response**:
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

### RAG Chat

```http
POST /chat/
Content-Type: application/json

{
  "query": "What is Python used for in AI?",
  "conversation_id": null,
  "top_k": 5,
  "use_web_search": false
}
```

**Parameters**:
- `query` (required): Question
- `conversation_id` (optional): UUID for follow-up questions (null for new conversation)
- `top_k` (optional): Number of context chunks (default: 5)
- `use_web_search` (optional): Include web search results via Tavily (default: false)

**Response**:
```json
{
  "answer": "Python is widely used in AI for...",
  "conversation_id": "uuid",
  "sources": [
    {
      "type": "document",
      "document_id": "uuid",
      "document_title": "Python Guide",
      "content": "Python has emerged as...",
      "score": 0.92
    },
    {
      "type": "web",
      "title": "Python in AI - 2026 Guide",
      "url": "https://example.com/python-ai",
      "content": "Python dominates AI development...",
      "score": 0.88
    }
  ],
  "model": "amazon.nova-micro-v1:0"
}
```

**Source Types**:
- `document`: From your uploaded documents
- `web`: From Tavily web search (only if `use_web_search: true`)

**Example - New Conversation**:
```bash
curl -X POST https://your-api/dev/chat/ \
  -H "Content-Type: application/json" \
  -d '{"query": "What is Python used for in AI?"}'
```

**Example - With Web Search**:
```bash
curl -X POST https://your-api/dev/chat/ \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the latest AI trends?",
    "use_web_search": true
  }'
```

**Example - Follow-up**:
```bash
curl -X POST https://your-api/dev/chat/ \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Tell me more about that",
    "conversation_id": "uuid-from-previous-response"
  }'
```

---

### List Conversations

```http
GET /chat/conversations/
```

Lists all conversations with basic metadata.

**Response**:
```json
[
  {
    "conversation_id": "uuid",
    "user_id": "anonymous",
    "message_count": 4,
    "created_at": "2026-02-01T12:00:00Z",
    "updated_at": "2026-02-01T12:05:00Z"
  }
]
```

**Notes**:
- Sorted by most recently updated first
- Shows total message count (user + assistant messages)

---

### Get Conversation

```http
GET /chat/conversations/{conversation_id}
```

Retrieves a specific conversation with all messages.

**Response**:
```json
{
  "conversation_id": "uuid",
  "user_id": "anonymous",
  "messages": [
    {
      "role": "user",
      "content": "What is Python?",
      "timestamp": "2026-02-01T12:00:00Z"
    },
    {
      "role": "assistant",
      "content": "Python is a programming language...",
      "timestamp": "2026-02-01T12:00:05Z"
    }
  ],
  "created_at": "2026-02-01T12:00:00Z",
  "updated_at": "2026-02-01T12:00:05Z"
}
```

---

### Delete Conversation

```http
DELETE /chat/conversations/{conversation_id}
```

Deletes a conversation and all its messages.

**Response**:
```json
{
  "conversation_id": "uuid",
  "deleted": true,
  "message": "Conversation deleted successfully"
}
```

---

## Error Responses

All errors return consistent format:

```json
{
  "error": {
    "type": "ErrorType",
    "message": "Human-readable error message",
    "details": {"key": "value"}
  }
}
```

### Common Error Types

| Error Type | HTTP Status | Description |
|------------|-------------|-------------|
| `DocumentNotFoundException` | 404 | Document not found |
| `InvalidFileTypeException` | 400 | Unsupported file format |
| `FileSizeExceededException` | 413 | File too large (>10MB) |
| `FileProcessingException` | 422 | Text extraction failed |
| `EmptyDocumentException` | 400 | No extractable content |
| `DatabaseException` | 503 | DynamoDB error |
| `VectorStoreException` | 503 | FAISS error |
| `EmbeddingException` | 503 | Embedding generation failed |
| `InvalidSearchQueryException` | 400 | Invalid query parameters |
| `ServiceUnavailableException` | 503 | External service unavailable |

---

## Rate Limits

- **Steady state**: 100 requests/second
- **Burst**: 200 requests/second
- **Lambda timeout**: 5 minutes
- **API Gateway timeout**: 30 seconds

---

## Interactive Documentation

After deployment, access:
- **Swagger UI**: `https://your-api/dev/docs`
- **ReDoc**: `https://your-api/dev/redoc`
- **OpenAPI JSON**: `https://your-api/dev/openapi.json`

---

## Notes

### First Request Timeout
First request after cold start may timeout (30s). Retry after 5 seconds.

### PDF Limitations
Some PDFs with font issues may fail. Convert to TXT or DOCX as workaround.

### Data Retention
All data auto-deletes after 15 days (DynamoDB TTL + S3 lifecycle).

---

## Testing

```bash
# 1. Health check
curl https://your-api/dev/health/

# 2. Upload document
curl -X POST https://your-api/dev/documents/upload \
  -F "file=@test.txt"

# 3. List documents
curl https://your-api/dev/documents/

# 4. Search
curl -X POST https://your-api/dev/search/ \
  -H "Content-Type: application/json" \
  -d '{"query": "your search query"}'

# 5. Chat
curl -X POST https://your-api/dev/chat/ \
  -H "Content-Type: application/json" \
  -d '{"query": "your question"}'

# 6. Delete document
curl -X DELETE https://your-api/dev/documents/{document_id}

# 7. List conversations
curl https://your-api/dev/chat/conversations/

# 8. Get conversation
curl https://your-api/dev/chat/conversations/{conversation_id}

# 9. Delete conversation
curl -X DELETE https://your-api/dev/chat/conversations/{conversation_id}
```
