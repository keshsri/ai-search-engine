# Tavily Web Search Integration

This document explains the Tavily web search integration added to the AI Semantic Search Engine.

## Overview

The system now supports hybrid search combining:
- **Document Search**: Semantic search over your uploaded documents (existing)
- **Web Search**: Real-time web search via Tavily API (new)

This enables the AI to answer questions using both your private documents and current web information.

## Architecture

```
User Query
    ↓
    ├─→ Semantic Search (Your Documents) → Top 5 chunks
    └─→ Tavily Search (Web, optional) → Top 3 results
    ↓
Combined Context (up to 8 sources)
    ↓
Bedrock (Amazon Nova Micro) → Answer with citations
    ↓
Response with sources marked as "document" or "web"
```

## Setup Instructions

### 1. Get Tavily API Key

1. Sign up at [https://tavily.com](https://tavily.com)
2. Get your API key from the dashboard
3. Free tier includes 1,000 searches/month

### 2. Add to GitHub Secrets

1. Go to your GitHub repository
2. Navigate to: **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Name: `TAVILY_API_KEY`
5. Value: Your Tavily API key (e.g., `tvly-xxxxxxxxxxxxx`)
6. Click **Add secret**

### 3. Deploy

The GitHub Actions workflow will automatically pass the secret to CDK during deployment:

```bash
# Trigger deployment
git push origin main
# or manually trigger via GitHub Actions UI
```

### 4. Local Development (Optional)

For local testing, add to your `.env` file:

```bash
# services/search_api/.env
TAVILY_API_KEY=tvly-xxxxxxxxxxxxx
```

**Important**: Never commit `.env` files to Git!

## API Usage

### Chat Endpoint

The `/chat/` endpoint now accepts an optional `use_web_search` parameter:

```bash
curl -X POST https://your-api/dev/chat/ \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the latest trends in AI?",
    "use_web_search": true,
    "top_k": 5
  }'
```

**Parameters:**
- `query` (required): User's question
- `use_web_search` (optional): Enable web search (default: `false`)
- `conversation_id` (optional): For follow-up questions
- `top_k` (optional): Number of document chunks to retrieve (default: 5)

**Response:**

```json
{
  "answer": "Based on your documents and web sources...",
  "conversation_id": "uuid",
  "sources": [
    {
      "type": "document",
      "document_id": "uuid",
      "document_title": "AI Report 2024",
      "content": "...",
      "score": 0.92
    },
    {
      "type": "web",
      "title": "Latest AI Trends",
      "url": "https://example.com/ai-trends",
      "content": "...",
      "score": 0.88
    }
  ],
  "model": "amazon.nova-micro-v1:0"
}
```

## Frontend Usage

The Streamlit UI includes a **🌐 Web** toggle in the chat interface:

1. Enable the toggle to include web search results
2. Ask your question
3. The AI will use both your documents and web sources
4. Sources are clearly labeled as "From Your Documents" or "From Web Search"

## Implementation Details

### Service Layer

**TavilyService** (`app/services/tavily_service.py`):
- Singleton pattern for client reuse
- Graceful degradation if API key not configured
- Error handling for API failures
- Response normalization to internal data models

**Key Patterns Demonstrated:**
- External API integration with HTTP client
- API key authentication via environment variables
- Error handling and fallback strategies
- Response parsing and data transformation

### Security

**API Key Storage:**
- ✅ Stored in GitHub Secrets (encrypted)
- ✅ Passed to Lambda via CDK context
- ✅ Never exposed in logs or code
- ✅ Not accessible to unauthorized users

**Best Practices:**
- API key loaded from environment variables
- Graceful fallback if key not configured
- No hardcoded credentials
- Follows same pattern as AWS Bedrock integration

### Cost Considerations

**Tavily Pricing:**
- Free tier: 1,000 searches/month
- Paid: $0.001 per search after free tier

**Typical Usage:**
- Web search is opt-in (not enabled by default)
- ~100-200 searches/month for moderate usage
- Stays within free tier for most users

## Error Handling

The system handles various failure scenarios:

1. **API Key Not Configured**: Web search disabled, documents-only search works
2. **Tavily API Failure**: Graceful degradation, continues with document search
3. **Rate Limit Exceeded**: Returns error, suggests trying again later
4. **Network Timeout**: Falls back to document-only search

## Testing

### Test Web Search

```bash
# Test with web search enabled
curl -X POST http://localhost:8000/chat/ \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the current weather in San Francisco?",
    "use_web_search": true
  }'
```

### Test Without Web Search

```bash
# Test document-only search (default)
curl -X POST http://localhost:8000/chat/ \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What does my document say about AI?",
    "use_web_search": false
  }'
```

## Troubleshooting

### Web Search Not Working

1. **Check API Key**: Verify `TAVILY_API_KEY` is set in GitHub Secrets
2. **Check Logs**: Look for "Tavily service not available" in CloudWatch
3. **Verify Deployment**: Ensure CDK deployed with `--context tavilyApiKey=...`
4. **Test Locally**: Try with `.env` file to isolate deployment issues

### Rate Limit Errors

If you exceed Tavily's rate limits:
- Free tier: 1,000 searches/month
- Solution: Upgrade Tavily plan or reduce web search usage

## Future Enhancements

Potential improvements:
- **Smart Query Routing**: Auto-detect when web search is needed (keywords like "latest", "current")
- **Result Reranking**: Combine and rerank document + web results
- **Caching**: Cache web search results to reduce API calls
- **Source Quality Scoring**: Prioritize authoritative web sources

## Learning Resources

This integration demonstrates:
- External API integration patterns
- Secure credential management
- Hybrid search architectures
- Graceful degradation strategies
- Error handling best practices

Compare with the existing Bedrock integration to see:
- AWS SDK (boto3) vs REST API patterns
- IAM authentication vs API key authentication
- Different error handling approaches

## References

- [Tavily API Documentation](https://docs.tavily.com)
- [GitHub Secrets Documentation](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [AWS CDK Context](https://docs.aws.amazon.com/cdk/v2/guide/context.html)
