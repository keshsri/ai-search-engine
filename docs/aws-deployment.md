# AWS Deployment Guide

## Architecture

100% serverless architecture designed for AWS Free Tier:

```
Client → API Gateway → Lambda (Docker)
                         ├─ DynamoDB (3 tables)
                         ├─ S3 (files + FAISS index)
                         └─ Bedrock (Claude 3.5 Haiku)
```

## Prerequisites

1. AWS Account with Bedrock access
2. AWS CLI configured
3. Docker installed
4. Node.js 18+ and npm
5. AWS CDK installed globally

## Free Tier Limits

| Service | Free Tier | Expected Usage |
|---------|-----------|----------------|
| Lambda | 1M requests/month | ~50K/month |
| API Gateway | 1M requests/month | ~50K/month |
| DynamoDB | 25GB + 200M requests | <1GB + 100K |
| S3 | 5GB + 20K GET + 2K PUT | ~2GB + 10K |
| CloudWatch | 5GB logs | ~1GB/month |

## Infrastructure Components

### DynamoDB Tables
- `ai-search-documents`: Document metadata
- `document_chunks`: Text chunks
- `conversations`: Chat history
- Billing: Pay-per-request (on-demand)

### S3 Bucket
- Uploaded files
- FAISS index + metadata
- Lifecycle: 90-day expiration
- Encryption: AES-256

### Lambda Function
- Runtime: Python 3.12 (Docker)
- Memory: 3GB
- Timeout: 5 minutes
- Image size: ~2-3GB

### API Gateway
- Type: REST API
- Stage: dev
- Throttling: 100 req/s steady, 200 burst
- CORS: Enabled

## Deployment Steps

### 1. Install Dependencies

```bash
cd infra/cdk
npm install
```

### 2. Bootstrap CDK (First Time Only)

```bash
cdk bootstrap
```

### 3. Deploy

```bash
# Preview changes
cdk diff

# Deploy
cdk deploy
```

Deployment takes 10-15 minutes (Docker build + upload).

### 4. Get API Endpoint

After deployment, CDK outputs:

```
Outputs:
SearchInfraStack.ApiEndpoint = https://xxx.execute-api.region.amazonaws.com/dev/
```

Save this endpoint for testing.

## Testing

```bash
# Health check
curl https://YOUR-API-ENDPOINT/health/

# Upload document
curl -X POST "https://YOUR-API-ENDPOINT/documents/upload" \
  -F "file=@test.txt"

# Search
curl -X POST "https://YOUR-API-ENDPOINT/search/" \
  -H "Content-Type: application/json" \
  -d '{"query": "your query", "top_k": 5}'

# Chat
curl -X POST "https://YOUR-API-ENDPOINT/chat/" \
  -H "Content-Type: application/json" \
  -d '{"query": "your question"}'
```

## Cost Monitoring

### Set Up Billing Alerts

1. Go to AWS Billing Console
2. Create budget alert for $5/month
3. Receive email notifications

### Monitor Usage

```bash
# Lambda invocations
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=ai-search-api \
  --start-time 2026-01-01T00:00:00Z \
  --end-time 2026-01-31T23:59:59Z \
  --period 86400 \
  --statistics Sum
```

## Cold Start Optimization

### Current Strategy
- Model downloaded during Docker build
- FAISS loaded from S3 on cold start
- 3GB memory allocation

### Expected Times
- First invocation: 5-10 seconds
- Warm invocations: <100ms
- Cold start frequency: ~1 per 15 minutes

### Optimization Options
1. Provisioned concurrency (costs money)
2. Scheduled pings (CloudWatch Events)
3. Smaller embedding model

## Updating

### Code Changes

```bash
cd infra/cdk
cdk deploy
```

CDK rebuilds Docker image and updates Lambda.

### Infrastructure Changes

Modify `infra/cdk/lib/search-infra-stack.ts`, then:

```bash
cdk diff  # Preview
cdk deploy  # Apply
```

## Cleanup

Delete all resources:

```bash
cd infra/cdk
cdk destroy
```

**Warning**: This deletes all data (DynamoDB tables, S3 files).

## Troubleshooting

### Lambda Timeout
Check CloudWatch Logs:
```bash
aws logs tail /aws/lambda/ai-search-api --follow
```

### Out of Memory
Increase `memorySize` in CDK stack (max 10GB).

### Docker Build Fails
- Ensure Docker is running
- Check disk space (~3GB needed)
- Try local build: `cd services/search_api && docker build -f Dockerfile.lambda .`

### API Gateway 502
- Check Lambda logs
- Verify IAM permissions
- Test Lambda directly: `aws lambda invoke --function-name ai-search-api response.json`

## Security Best Practices

1. Add API keys for production
2. Restrict CORS origins
3. Use least-privilege IAM roles
4. Enable S3 bucket encryption
5. Review CloudTrail logs regularly

## Cost Estimate

Within Free Tier:
- Lambda: $0
- API Gateway: $0
- DynamoDB: $0
- S3: $0
- Bedrock: ~$0.003 per query

Typical usage: <$5/month

After Free Tier expires:
- Lambda: ~$0.20/month
- API Gateway: ~$0.18/month
- DynamoDB: Free (Always Free tier)
- S3: ~$0.05/month
- **Total**: ~$0.50/month + Bedrock usage
