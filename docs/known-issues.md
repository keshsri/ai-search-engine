# Known Issues and Limitations

## 1. Cold Start Timeout

**Issue**: First request after Lambda cold start times out with 504 Gateway Timeout.

**Root Cause**:
- API Gateway: 30-second hard timeout
- Model loading: ~20 seconds
- Request processing: ~5-10 seconds

**Impact**: First request to embedding endpoints fails. Subsequent requests succeed.

**Workaround**:
1. Make request (will timeout)
2. Wait 5 seconds
3. Retry (will succeed)

**Note**: For higher availability, consider provisioned concurrency (~$15/month).

---

## 2. PDF Extraction Failures

**Issue**: Some PDFs fail with "no extractable text" error.

**Root Cause**:
- Font encoding issues
- Scanned PDFs (no text layer)
- Malformed PDF structure

**Workaround**:
- Convert PDF to TXT locally
- Use DOCX format instead
- Re-export PDF from Adobe Acrobat

**Note**: AWS Textract integration would solve this (~$1.50 per 1K pages).

---

## 3. No Authentication

**Issue**: API is publicly accessible.

**Impact**:
- No user tracking
- No per-user rate limiting
- Anyone can upload/search

---

## 4. Lambda Container Lifecycle

**Behavior**: Lambda containers reused for ~15-30 minutes, then expire.

**Impact**:
- First request to new container: Slow (~20-30s)
- Subsequent requests: Fast (<1s)
- After expiration: Back to slow

**This is expected Lambda behavior.**

**Implications**:
- `/tmp` directory persists within container lifetime
- In-memory state (model, FAISS) persists
- FAISS index reloaded from S3 after expiration

---

## 5. API Gateway Timeout Limit

**Limitation**: 30-second hard timeout (cannot be increased).

**Impact**:
- Long-running requests fail
- Affects cold starts
- Large document uploads may approach limit

**Alternatives**:
- Lambda function URLs (15-minute timeout)
- Application Load Balancer (15-minute timeout)
- Async processing with SQS

---

## 6. FAISS Scalability

**Current**: IndexFlatL2 (exact search, O(n) complexity)

**Limitations**:
- Performance degrades with >100K vectors
- No approximate search

**Future Improvements**:
- IndexIVFFlat for approximate search
- Managed vector DB (Pinecone, Weaviate, OpenSearch)

---

## 7. No Conversation Expiration

**Issue**: Conversations stored indefinitely in DynamoDB.

**Impact**: Storage costs increase over time.

**Solution**:
- DynamoDB TTL attribute
- Scheduled Lambda for cleanup
- Manual deletion via API

---

## 8. Memory Usage

**Configuration**: 3GB Lambda memory

**Typical Usage**: ~1.3GB (model + dependencies)

**Considerations**:
- Cannot reduce below 2GB without OOM errors
- Multiple concurrent requests share container memory

---

## Summary

**Critical Issues**:
1. Cold start timeout (workaround: retry)
2. PDF extraction failures (workaround: convert to TXT)

**Minor Limitations**:
3. No authentication (acceptable for portfolio)
4. API Gateway 30s timeout (architectural limit)
5. FAISS scalability (suitable for <100K vectors)

**Non-Issues**:
6. Lambda cold starts (expected behavior)
7. Container reuse (expected behavior)

---

## Troubleshooting

Check CloudWatch Logs:
```bash
aws logs tail /aws/lambda/ai-search-api --follow
```

Monitor metrics in AWS Console:
- Lambda invocations, errors, duration
- API Gateway 4xx/5xx errors
- DynamoDB read/write capacity
