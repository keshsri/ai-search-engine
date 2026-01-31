# Search API Service

FastAPI-based semantic search engine with RAG capabilities.

## Features

- Document ingestion (PDF, DOCX, TXT)
- Text chunking with overlap
- Semantic embeddings (sentence-transformers)
- Vector similarity search (FAISS)
- RAG-powered Q&A (AWS Bedrock)
- Conversation history management

## Local Development

### Prerequisites

- Python 3.12+
- pip

### Setup

```bash
# Install dependencies
python -m pip install -r requirements.txt

# Run locally
uvicorn app.main:app --reload
```

### Access

- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
app/
├── api/              # API endpoints
│   ├── health.py     # Health check
│   ├── documents.py  # Document CRUD
│   ├── search.py     # Semantic search
│   └── chat.py       # RAG chat
├── core/             # Core configuration
│   ├── config.py     # Settings
│   ├── logging.py    # Logging setup
│   ├── exceptions.py # Custom exceptions
│   └── error_handlers.py
├── db/               # Database layer
│   ├── dynamodb.py   # DynamoDB client
│   └── models.py     # Data models
├── models/           # Pydantic models
│   ├── document.py
│   ├── search.py
│   └── conversation.py
├── services/         # Business logic
│   ├── chunking_service.py
│   ├── embedding_service.py
│   ├── file_processor.py
│   ├── search_service.py
│   ├── bedrock_service.py
│   └── conversation_service.py
├── vector_store/     # FAISS integration
│   └── faiss_store.py
├── dependencies.py   # FastAPI dependencies
├── lambda_handler.py # Lambda entry point
└── main.py          # FastAPI app
```

## Environment Variables

```bash
# AWS
AWS_REGION=us-east-1
DYNAMODB_DOCUMENT_TABLE=ai-search-documents
CHUNKS_TABLE_NAME=document_chunks
CONVERSATIONS_TABLE_NAME=conversations
DOCUMENTS_BUCKET=your-bucket-name

# Chunking
CHUNK_SIZE=300

# Embeddings
EMBEDDING_DIMENSION=384

# FAISS
FAISS_TOP_K=5

# Bedrock
BEDROCK_MODEL_ID=anthropic.claude-3-5-haiku-20241022-v1:0
BEDROCK_MAX_TOKENS=1000
BEDROCK_TEMPERATURE=0.7
```

## Testing

```bash
# Health check
curl http://localhost:8000/health/

# Upload document
curl -X POST http://localhost:8000/documents/upload \
  -F "file=@test.txt"

# Search
curl -X POST http://localhost:8000/search/ \
  -H "Content-Type: application/json" \
  -d '{"query": "test query", "top_k": 5}'

# Chat
curl -X POST http://localhost:8000/chat/ \
  -H "Content-Type: application/json" \
  -d '{"query": "test question"}'
```

## Docker

### Build

```bash
docker build -f Dockerfile.lambda -t search-api .
```

### Run Locally

```bash
docker run -p 9000:8080 \
  -e AWS_REGION=us-east-1 \
  -e DYNAMODB_DOCUMENT_TABLE=ai-search-documents \
  search-api
```

### Test Lambda Handler

```bash
curl -X POST "http://localhost:9000/2015-03-31/functions/function/invocations" \
  -d '{"path": "/health/", "httpMethod": "GET"}'
```

## Dependencies

- **FastAPI**: Web framework
- **Mangum**: AWS Lambda adapter
- **boto3**: AWS SDK
- **sentence-transformers**: Embeddings
- **faiss-cpu**: Vector search
- **pdfplumber**: PDF extraction
- **python-docx**: DOCX extraction
- **nltk**: Text processing

## Notes

- First request after cold start may be slow (~20s)
- Model loaded once per Lambda container
- FAISS index loaded from S3 on demand
- Conversation history persists in DynamoDB
