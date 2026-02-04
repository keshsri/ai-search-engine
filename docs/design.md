# OmniSearch AI - System Design

**Status**: Implemented  
**Last Updated**: February 2026

## 1. Executive Summary

OmniSearch AI is an intelligent search engine with RAG capabilities that enables natural language queries over document collections and real-time web search. Users can upload documents (PDF, DOCX, TXT), perform semantic search, and receive AI-generated answers grounded in their content or current web information.

**Key Technologies**: FastAPI, AWS Lambda, DynamoDB, S3, FAISS, sentence-transformers, AWS Bedrock (Amazon Nova Micro), Tavily (Web Search)

## 2. Problem Statement

Traditional keyword search fails to understand semantic meaning, intent, and context. Users need:
- Natural language queries that understand intent
- Direct answers instead of document lists
- Access to both private documents and current web information
- Source attribution for verification
- Conversational follow-up questions

This system bridges the gap using semantic embeddings, RAG, and hybrid search (documents + web) to provide accurate, grounded responses.

## 3. Architecture

### High-Level Design

```
Client (HTTP/HTTPS)
    ↓
API Gateway (REST API)
    ├─ Throttling: 100 req/s steady, 200 req/s burst
    └─ Timeout: 30 seconds
    ↓
Lambda Function (Docker, 3GB memory, 5min timeout)
    ├─ FastAPI application
    ├─ sentence-transformers (all-MiniLM-L6-v2)
    ├─ FAISS vector store
    └─ Tavily client (web search)
    ↓
├─ DynamoDB (3 tables)
│   ├─ documents (metadata)
│   ├─ chunks (text chunks)
│   └─ conversations (chat history)
│
├─ S3 Bucket
│   ├─ Uploaded files
│   └─ FAISS index + metadata
│
├─ AWS Bedrock
│   └─ Amazon Nova Micro (LLM)
│
└─ Tavily API
    └─ Web search results
```

### Component Responsibilities

**API Gateway**: Request routing, throttling, CORS, logging

**Lambda**: Stateless processing, text extraction, chunking, embeddings, vector search, web search, LLM orchestration

**DynamoDB**: Document metadata, text chunks, conversation history (pay-per-request billing)

**S3**: File storage, FAISS index persistence

**Bedrock**: LLM inference for answer generation

**Tavily**: Real-time web search for current information

## 4. Data Flow

### Document Ingestion

1. Client uploads file (PDF/DOCX/TXT)
2. Lambda extracts text (pdfplumber, python-docx)
3. Text chunked (300 chars, 50 char overlap)
4. Generate embeddings (384-dim vectors)
5. Store in DynamoDB + FAISS + S3
6. Return document_id

### Semantic Search

1. Client sends query
2. Generate query embedding
3. FAISS similarity search (top-K)
4. Fetch chunk metadata from DynamoDB
5. Return ranked results with scores

### RAG Chat

1. Client sends query + optional conversation_id + optional use_web_search flag
2. Retrieve relevant chunks (semantic search)
3. If web search enabled, fetch results from Tavily
4. Load conversation history (if exists)
5. Build prompt: document context + web context + history + query
6. Call Bedrock (Amazon Nova Micro)
7. Save conversation to DynamoDB
8. Return answer + sources (documents and/or web) + conversation_id

## 5. Core Components

### Text Chunker
- **Algorithm**: Fixed 300-char chunks with 50-char overlap
- **Rationale**: Balances context vs. granularity, prevents sentence splitting
- **Output**: chunk_id, document_id, content, index

### Embedding Service
- **Model**: sentence-transformers/all-MiniLM-L6-v2 (384-dim, ~80MB)
- **Pattern**: Singleton (load once per Lambda container)
- **Cache**: In-memory for container lifetime (~15-30 min)

### Vector Store
- **Index**: FAISS IndexFlatL2 (exact L2 distance)
- **Persistence**: In-memory + S3 backup
- **Trade-off**: Accuracy over speed (suitable for <100K vectors)

### Bedrock Service
- **Model**: Amazon Nova Micro ($0.035/M input, $0.14/M output tokens)
- **Config**: Max 3000 tokens, temperature 0.7
- **Prompt**: System instructions + context + history + query

### Conversation Service
- **Storage**: DynamoDB (messages as list for atomic updates)
- **Context**: Last 5 messages included in LLM prompts
- **Expiration**: 15-day TTL (auto-deletion)

### Tavily Service
- **API**: REST API with API key authentication
- **Search Depth**: Basic (fast) or Advanced (comprehensive)
- **Results**: Top 3 web results per query
- **Caching**: No caching (always fresh results)
- **Cost**: Free tier 1,000 searches/month

## 6. API Design

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health/` | Health check |
| GET | `/documents/` | List all documents |
| POST | `/documents/` | Ingest from JSON |
| POST | `/documents/upload` | Upload file |
| GET | `/documents/{id}` | Get document |
| DELETE | `/documents/{id}` | Delete document |
| POST | `/search/` | Semantic search |
| POST | `/chat/` | RAG Q&A |

### Error Response Format

```json
{
  "error": {
    "type": "ErrorType",
    "message": "Human-readable message",
    "details": {"key": "value"}
  }
}
```

## 7. Infrastructure as Code

### AWS CDK Stack

**DynamoDB Tables**:
- Pay-per-request billing
- DESTROY removal policy
- No point-in-time recovery
- 15-day TTL on all tables

**S3 Bucket**:
- AES-256 encryption
- 15-day lifecycle policy
- Public access blocked

**Lambda**:
- Python 3.12 Docker container
- 3GB memory, 5-minute timeout
- Environment variables for config

**API Gateway**:
- REST API with /dev stage
- Throttling configured
- CloudWatch logging enabled (3-day retention)

**IAM**:
- Least privilege permissions
- DynamoDB read/write
- S3 read/write
- Bedrock InvokeModel

### Deployment

**GitHub Actions** (OIDC authentication):
1. Checkout code
2. Setup Node.js + Python
3. Configure AWS credentials (no static keys)
4. Install dependencies
5. CDK deploy

**Trigger**: Push to main branch or manual dispatch

**Duration**: ~15-20 minutes (Docker build + deploy)

## 8. Performance & Scalability

### Performance Characteristics

**Warm Lambda**:
- Document upload: 500-1000ms
- Search: 100-300ms
- Chat: 1-2 seconds

**Cold Lambda**:
- Model loading: ~20 seconds
- First request: May timeout (30s limit)
- Workaround: Retry after 5 seconds

### Scalability

**Auto-scaling**:
- Lambda: Up to 1000 concurrent executions
- DynamoDB: Pay-per-request (no limits)
- API Gateway: 10,000 req/s regional limit

**Bottlenecks**:
- FAISS: O(n) search (acceptable for <100K vectors)
- Bedrock: Model-specific rate limits
- Cold starts: ~20-30 seconds

## 9. Security

### Authentication
- **Current**: None (public API)

### IAM
- No static credentials (OIDC for CI/CD)
- Lambda uses IAM role
- Least privilege permissions

### Data Security
- S3: AES-256 encryption at rest
- DynamoDB: AWS managed encryption
- API Gateway: HTTPS only (TLS 1.2+)
- No PII stored
- 15-day auto-deletion (TTL)

## 10. Cost Analysis

### AWS Free Tier

| Service | Free Tier | Typical Usage | Cost |
|---------|-----------|---------------|------|
| Lambda | 1M req/month | 3K req/month | $0 |
| API Gateway | 1M req/month | 3K req/month | $0 |
| DynamoDB | 25GB storage | <1GB | $0 |
| S3 | 5GB storage | <1GB | $0 |
| Bedrock | None | 100 queries | $0.01 |

**Total**: ~$0.01-$2/month depending on usage

### Cost Optimization

- Serverless (no idle costs)
- Pay-per-request DynamoDB
- 3-day log retention
- 15-day S3 lifecycle + DynamoDB TTL
- Efficient chunking
- Amazon Nova Micro (cheapest LLM)

## 11. Known Limitations

### 1. Cold Start Timeout
- **Issue**: First request after 15min inactivity times out
- **Cause**: Model loading (~20s) + API Gateway 30s limit
- **Workaround**: Retry after 5 seconds
- **Solution**: Provisioned concurrency or EventBridge warming

### 2. PDF Extraction
- **Issue**: Some PDFs fail extraction
- **Cause**: Font encoding issues, scanned PDFs
- **Workaround**: Convert to TXT or DOCX
- **Solution**: AWS Textract integration

### 3. No Authentication
- **Issue**: Public API
- **Impact**: No user tracking or rate limiting

### 4. FAISS Scalability
- **Current**: Exact search, O(n) complexity
- **Limit**: Performance degrades >100K vectors
- **Solution**: Approximate search or managed vector DB

## 12. Design Decisions

### Serverless vs. Container
- **Choice**: Serverless (Lambda)
- **Rationale**: Zero idle costs, auto-scaling, minimal ops
- **Trade-off**: Cold starts, 30s API Gateway timeout

### FAISS vs. Managed Vector DB
- **Choice**: FAISS (in-memory + S3)
- **Rationale**: Zero cost, simple deployment
- **Trade-off**: Must rebuild on ingestion, limited scalability

### Bedrock vs. OpenAI
- **Choice**: AWS Bedrock
- **Rationale**: IAM auth, same AWS account, competitive pricing
- **Trade-off**: Requires model access request

### DynamoDB vs. RDS
- **Choice**: DynamoDB
- **Rationale**: Serverless, pay-per-request, auto-scaling
- **Trade-off**: No complex queries, eventual consistency

## 13. Future Enhancements

**Short-term**:
- Streamlit frontend
- Query caching

**Medium-term**:
- API key authentication
- Result reranking
- Document management UI

**Long-term**:
- Multi-modal support (images, OCR)
- Advanced RAG (query decomposition, HyDE)
- Managed vector DB migration
- Multi-tenancy

## 14. Conclusion

This system demonstrates modern engineering practices: serverless architecture, infrastructure-as-code, comprehensive error handling, and secure-by-default design.

**Key Strengths**:
- Stateless, horizontally scalable
- Cost-effective (<$2/month with auto-deletion)
- Secure (no credentials, IAM-only)
- Well-documented and maintainable
- Full RAG implementation with conversation memory
