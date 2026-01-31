# Known Issues and Limitations

This document outlines known issues, limitations, and workarounds for the AI Semantic Search API.

---

## 1. First Request Timeout After Cold Start

**Issue:**
The first API request after a Lambda cold start (or after ~15 minutes of inactivity) will timeout with a 504 Gateway Timeout error.

**Root Cause:**
- API Gateway has a hard 30-second timeout limit
- Loading the sentence-transformers model into memory takes ~20 seconds
- Combined with request processing time, this exceeds the 30-second limit

**Impact:**
- First request to any endpoint that uses embeddings (`/documents/upload`, `/documents/`, `/search/`) will fail
- Subsequent requests work normally (model cached in memory)
- Health endpoint (`/health/`) is not affected

**Workaround:**
1. Make a request (it will timeout)
2. Wait 5 seconds
3. Retry the same request (will succeed)

**Example:**
```bash
# First request - will timeout
curl -X POST https://your-api.com/dev/documents/upload -F "file=@doc.txt"
# Response: {"message": "Endpoint request timed out"}

# Wait 5 seconds, then retry
curl -X POST https://your-api.com/dev/documents/upload -F "file=@doc.txt"
# Response: Success!
```

**Production Solutions:**
- **EventBridge warming:** Ping the API every 5 minutes to keep Lambda warm
- **Provisioned concurrency:** Keep Lambda always warm (costs ~$15/month)
- **Smaller model:** Use a lighter embedding model (trade-off: lower quality)

---

## 2. PDF Extraction Issues

**Issue:**
Some PDFs fail to extract text with error: "PDF contains no extractable text"

**Root Cause:**
PDFs with font encoding issues or malformed font descriptors may fail extraction even though they appear to have text when viewed locally.

**Affected PDFs:**
- PDFs with custom/embedded fonts that have missing FontBBox descriptors
- PDFs created by certain tools that don't follow strict PDF standards
- Scanned/image-based PDFs (no text layer)

**Impact:**
- Document upload fails for affected PDFs
- Error message: `"PDF contains no extractable text (pdfplumber)"`

**Workaround:**
1. **Convert to TXT:** Extract text locally and upload as TXT file
2. **Use DOCX:** Convert PDF to DOCX format
3. **Re-export PDF:** Open in Adobe Acrobat/Preview and export as new PDF

**Example Conversion Script:**
```python
import pdfplumber

# Extract PDF to TXT
with pdfplumber.open("document.pdf") as pdf:
    text = "\n\n".join([page.extract_text() for page in pdf.pages])
    
with open("document.txt", "w") as f:
    f.write(text)
```

**Production Solution:**
- Integrate AWS Textract for OCR support (handles scanned PDFs and problematic fonts)
- Cost: ~$1.50 per 1,000 pages

---

## 3. Lambda Init Timeout (Resolved)

**Issue:**
Lambda initialization was timing out with 10-second limit.

**Status:** ✅ **RESOLVED**

**Solution Implemented:**
- Lazy import of sentence-transformers (only imports when needed)
- Singleton pattern for EmbeddingService (loads once, reuses)
- NLTK data pre-downloaded to `/var/task/nltk_data` in Docker image
- Model pre-downloaded to `/var/task/sentence_transformers_cache` in Docker image

---

## 4. Container Reuse and State

**Behavior:**
Lambda containers are reused for multiple requests but eventually expire after ~15-30 minutes of inactivity.

**Impact:**
- First request to a new container: Slow (~20-30 seconds, may timeout)
- Subsequent requests to same container: Fast (<1 second)
- After container expires: Back to slow first request

**This is expected Lambda behavior, not a bug.**

**Implications:**
- `/tmp` directory persists across requests in same container
- In-memory state (singleton objects) persists across requests
- FAISS index and uploaded files in `/tmp` are lost when container expires
- S3 persistence ensures data survives container recycling

---

## 5. API Gateway 30-Second Timeout

**Limitation:**
API Gateway REST APIs have a hard 30-second timeout that cannot be increased.

**Impact:**
- Any request taking longer than 30 seconds will fail
- Affects first request after cold start (model loading)
- Large document uploads with many chunks may approach this limit

**Workaround:**
- Retry failed requests (subsequent attempts will be faster)
- For very large documents, consider splitting into smaller files

**Alternative:**
- Use API Gateway HTTP API (supports up to 30 seconds)
- Use Application Load Balancer (supports up to 15 minutes)
- Use Lambda function URLs (supports up to 15 minutes)

---

## 6. S3 Eventual Consistency

**Behavior:**
S3 operations are eventually consistent, meaning updates may not be immediately visible.

**Impact:**
- FAISS index updates may take 1-2 seconds to propagate
- Rare race condition: Search immediately after upload might not find new document

**Mitigation:**
- S3 is strongly consistent for new object PUTs (since Dec 2020)
- This is rarely an issue in practice
- If needed, add a small delay (1-2 seconds) between upload and search

---

## 7. Memory Usage

**Current Configuration:**
- Lambda memory: 3008 MB (3 GB)
- Typical usage: ~1.3 GB (model + dependencies)

**Considerations:**
- Cannot reduce memory below 2 GB without risking OOM errors
- Model loading requires significant memory
- Multiple concurrent requests share the same container memory

**Monitoring:**
- Check CloudWatch metrics for memory usage
- Alarm configured for high memory usage (>2.5 GB)

---

## 8. Cost Considerations

**Free Tier Usage:**
- Lambda: First 1M requests/month free
- API Gateway: First 1M requests/month free
- DynamoDB: 25 GB storage free
- S3: 5 GB storage free

**Potential Costs:**
- Lambda execution time: ~$0.20 per 1M requests (after free tier)
- S3 storage: ~$0.023 per GB/month (after 5 GB)
- DynamoDB: Pay-per-request pricing (very low for typical usage)

**With $140 AWS credits:**
- Estimated 6-month usage: $20-70
- Remaining buffer: $70-120

---

## 9. No LLM Integration (Yet)

**Current State:**
The API provides semantic search (retrieval) but does not generate answers using an LLM.

**What Works:**
- Document ingestion and chunking
- Semantic search with embeddings
- Returns relevant text chunks

**What's Missing:**
- Answer generation from retrieved chunks
- Conversational interface
- Context-aware responses

**Planned:**
- AWS Bedrock integration for LLM-powered answers
- Conversation history storage in DynamoDB
- `/chat/` endpoint for RAG-based Q&A

---

## 10. No Authentication

**Current State:**
The API is publicly accessible without authentication.

**Security Implications:**
- Anyone with the URL can use the API
- No rate limiting per user
- No usage tracking per user

**Acceptable For:**
- Portfolio/demo projects
- Internal testing
- Proof of concept

**Production Requirements:**
- Add API key authentication
- Implement JWT-based auth
- Add per-user rate limiting
- Use AWS WAF for DDoS protection

---

## Summary

**Critical Issues:**
1. First request timeout (workaround: retry)
2. Some PDFs fail extraction (workaround: convert to TXT)

**Minor Limitations:**
3. No LLM integration yet (planned)
4. No authentication (acceptable for portfolio)
5. API Gateway 30s timeout (architectural limit)

**Non-Issues:**
6. Lambda cold starts (expected behavior)
7. Container reuse (expected behavior)
8. S3 eventual consistency (rarely impacts usage)

---

## Reporting Issues

If you encounter issues not listed here, please check:
1. CloudWatch Logs: `/aws/lambda/ai-search-api`
2. API Gateway logs in CloudWatch
3. DynamoDB metrics in AWS Console

For persistent issues, review the error handling documentation in `docs/error-handling.md`.
