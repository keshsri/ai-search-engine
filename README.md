# AI Semantic Search Engine with RAG

A production-grade serverless semantic search engine that enables natural language queries over document collections using Retrieval-Augmented Generation (RAG).

## Features

- **Document Ingestion**: Upload PDF, DOCX, and TXT files with automatic text extraction
- **Semantic Search**: Natural language queries using sentence-transformer embeddings
- **RAG Chat**: AI-generated answers grounded in your documents using AWS Bedrock (Claude 3.5 Haiku)
- **Conversation History**: Multi-turn dialogues with context preservation
- **Serverless Architecture**: Auto-scaling, pay-per-use infrastructure on AWS

## Technology Stack

- **Backend**: FastAPI (Python 3.12)
- **Infrastructure**: AWS CDK (TypeScript)
- **Compute**: AWS Lambda (Docker containers)
- **Storage**: DynamoDB, S3, FAISS
- **AI/ML**: sentence-transformers, AWS Bedrock
- **CI/CD**: GitHub Actions with OIDC

## Quick Start

### Prerequisites

- AWS Account with Bedrock access
- Node.js 18+ and npm
- Python 3.12+
- Docker (for local development)

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
- `POST /documents/` - Ingest document from JSON
- `POST /documents/upload` - Upload file (PDF/DOCX/TXT)
- `GET /documents/{id}` - Retrieve document
- `DELETE /documents/{id}` - Delete document
- `POST /search/` - Semantic search
- `POST /chat/` - RAG-powered Q&A
- `GET /chat/conversations/{id}` - Conversation history

Interactive docs available at `/docs` (Swagger UI) and `/redoc`.

## Architecture

```
Client → API Gateway → Lambda (FastAPI)
                         ├─ DynamoDB (documents, chunks, conversations)
                         ├─ S3 (files, FAISS index)
                         └─ Bedrock (Claude 3.5 Haiku)
```

## Documentation

- [System Design](docs/design.md) - Architecture and design decisions
- [API Reference](docs/api-endpoints.md) - Complete API documentation
- [AWS Deployment](docs/aws-deployment.md) - Deployment guide
- [Known Issues](docs/known-issues.md) - Limitations and workarounds
- [Error Handling](docs/error-handling.md) - Error types and responses

## Known Limitations

- First request after cold start may timeout (retry after 5 seconds)
- Some PDFs with font issues may fail extraction (convert to TXT)
- No authentication (suitable for demo/portfolio projects)
- API Gateway has 30-second timeout limit

See [Known Issues](docs/known-issues.md) for details and workarounds.

## Cost Estimate

Within AWS Free Tier:
- Lambda: 1M requests/month free
- API Gateway: 1M requests/month free
- DynamoDB: 25 GB storage free
- S3: 5 GB storage free

Bedrock (Claude 3.5 Haiku): ~$0.003 per query

Typical usage: <$5/month

## License

MIT License - See LICENSE file for details

## Contributing

This is a portfolio project. Feel free to fork and adapt for your own use.
