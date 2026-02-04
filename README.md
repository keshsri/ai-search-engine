# AI Semantic Search Engine with RAG

A serverless semantic search engine that enables natural language queries over document collections using Retrieval-Augmented Generation (RAG).

Visit this [Wiki](https://deepwiki.com/keshsri/ai-search-engine) for complete and detailed AI generated documentation about this repositry.

## Features

- **Document Ingestion**: Upload PDF, DOCX, and TXT files with automatic text extraction
- **Semantic Search**: Natural language queries using sentence-transformer embeddings
- **RAG Chat**: AI-generated answers grounded in your documents using AWS Bedrock (Amazon Nova Micro)
- **Web Search Integration**: Optional real-time web search via Tavily API for current information
- **Conversation History**: Multi-turn dialogues with context preservation
- **Document Management**: List and delete documents with full cleanup
- **Serverless Architecture**: Auto-scaling, pay-per-use infrastructure on AWS
- **Auto-Deletion**: 15-day TTL on all data for cost optimization

## Technology Stack

- **Backend**: FastAPI (Python 3.12)
- **Frontend**: Streamlit (deployed on Streamlit Cloud)
- **Infrastructure**: AWS CDK (TypeScript)
- **Compute**: AWS Lambda (Docker containers)
- **Storage**: DynamoDB, S3, FAISS
- **AI/ML**: sentence-transformers, AWS Bedrock (Amazon Nova Micro)
- **CI/CD**: GitHub Actions with OIDC

## Quick Start

### Prerequisites

- AWS Account with Bedrock access
- Node.js 18+ and npm
- Python 3.12+
- Docker (for deployment via GitHub Actions)

### Local Development

```bash
# Install Python dependencies
cd services/search_api
python -m pip install -r requirements.txt

# Run locally
uvicorn app.main:app --reload
```

### AWS Deployment

```bash
# Install CDK dependencies
cd infra/cdk
npm install

# Bootstrap CDK (first time only)
cdk bootstrap

# Deploy
cdk deploy
```

See [AWS Deployment Guide](docs/aws-deployment.md) for detailed instructions.

## API Endpoints

- `GET /health/` - Health check
- `GET /documents/` - List all documents
- `POST /documents/` - Ingest document from JSON
- `POST /documents/upload` - Upload file (PDF/DOCX/TXT)
- `GET /documents/{id}` - Retrieve document
- `DELETE /documents/{id}` - Delete document and all associated data
- `POST /search/` - Semantic search
- `POST /chat/` - RAG-powered Q&A
- `GET /chat/conversations/` - List all conversations
- `GET /chat/conversations/{id}` - Get conversation with messages
- `DELETE /chat/conversations/{id}` - Delete conversation

Interactive docs available at `/docs` (Swagger UI) and `/redoc`.

## Architecture

```
Client → API Gateway → Lambda (FastAPI)
                         ├─ DynamoDB (documents, chunks, conversations)
                         ├─ S3 (files, FAISS index)
                         └─ Bedrock (Amazon Nova Micro)
```

## Documentation

- [System Design](docs/design.md) - Architecture and design decisions
- [API Reference](docs/api-endpoints.md) - Complete API documentation
- [Tavily Integration](docs/tavily-integration.md) - Web search setup and usage
- [AWS Deployment](docs/aws-deployment.md) - Deployment guide
- [Known Issues](docs/known-issues.md) - Limitations and workarounds
- [Error Handling](docs/error-handling.md) - Error types and responses

## Known Limitations

- First request after cold start may timeout (retry after 5 seconds)
- Some PDFs with font issues may fail extraction (convert to TXT)
- No authentication
- API Gateway has 30-second timeout limit

See [Known Issues](docs/known-issues.md) for details and workarounds.

## Cost Estimate

Within AWS Free Tier:
- Lambda: 1M requests/month free
- API Gateway: 1M requests/month free
- DynamoDB: 25 GB storage free
- S3: 5 GB storage free

Amazon Nova Micro: $0.035 input / $0.14 output per 1M tokens (~$0.0001 per query)

Typical usage: <$2/month with 15-day auto-deletion
