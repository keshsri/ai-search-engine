# AWS Serverless Deployment Guide

## Architecture Overview

This deployment uses a **100% serverless architecture** designed to stay within AWS Free Tier limits:

```
User Request
    ↓
API Gateway (1M requests/month free)
    ↓
Lambda Function (Docker) (1M requests + 400K GB-sec/month free)
    ├─ FastAPI Application
    ├─ Sentence Transformers Model (all-MiniLM-L6-v2)
    └─ FAISS Vector Store (loaded from S3)
    ↓
├─ DynamoDB (25 GB + 200M requests/month free)
│   ├─ ai-search-documents (document metadata)
│   └─ document_chunks (chunk metadata)
│
└─ S3 (5 GB storage + 20K GET + 2K PUT/month free)
    ├─ /uploads/* (uploaded documents)
    └─ /faiss/* (FAISS index + metadata)
```

## Free Tier Limits

| Service | Free Tier Limit | Expected Usage | Status |
|---------|----------------|----------------|--------|
| **Lambda** | 1M requests + 400K GB-sec/month | ~50K requests/month | ✅ Safe |
| **API Gateway** | 1M REST API calls/month | ~50K calls/month | ✅ Safe |
| **DynamoDB** | 25 GB + 200M requests/month | <1 GB + 100K requests | ✅ Safe |
| **S3** | 5 GB storage + 20K GET + 2K PUT | ~2 GB + 10K requests | ✅ Safe |
| **CloudWatch Logs** | 5 GB ingestion + storage | ~1 GB/month | ✅ Safe |

## Infrastructure Components

### 1. DynamoDB Tables
- **ai-search-documents**: Document metadata (partition key: document_id)
- **document_chunks**: Document chunks (partition key: document_id, sort key: chunk_id)
- **Billing**: PAY_PER_REQUEST (on-demand, no provisioned capacity)

### 2. S3 Bucket
- **Name**: `ai-search-documents-{account-id}`
- **Purpose**: Store uploaded files and FAISS index
- **Lifecycle**: Auto-delete files after 90 days
- **CORS**: Enabled for file uploads

### 3. Lambda Function
- **Name**: `ai-search-api`
- **Runtime**: Python 3.12 (Docker container)
- **Memory**: 3008 MB (3 GB for embedding model)
- **Timeout**: 300 seconds (5 minutes)
- **Handler**: `app.lambda_handler.handler`
- **Image Size**: ~2-3 GB (includes PyTorch + sentence-transformers)

### 4. API Gateway
- **Type**: REST API
- **Stage**: prod
- **Throttling**: 100 req/sec, 200 burst
- **CORS**: Enabled
- **Logging**: INFO level

### 5. CloudWatch Alarms
- **Lambda Invocations**: Alert at 30K/day (900K/month)
- **DynamoDB Reads**: Alert at 6M/day (180M/month)

## Prerequisites

1. **AWS Account** (created before July 15, 2025 for 12-month free tier)
2. **AWS CLI** configured with credentials
3. **Docker** installed and running
4. **Node.js** and **npm** installed
5. **AWS CDK** installed globally

## Deployment Steps

### Step 1: Install CDK Dependencies

```bash
cd infra/cdk
npm install
```

### Step 2: Bootstrap CDK (First Time Only)

```bash
cdk bootstrap
```

This creates the necessary S3 bucket and IAM roles for CDK deployments.

### Step 3: Build and Deploy

```bash
# Synthesize CloudFormation template
cdk synth

# Deploy the stack
cdk deploy
```

**Note**: The first deployment will take 10-15 minutes because:
- Docker image needs to be built (~2-3 GB)
- Image is pushed to ECR (Elastic Container Registry)
- Lambda function is created with the image

### Step 4: Get API Endpoint

After deployment, CDK will output:

```
Outputs:
SearchInfraStack.ApiEndpoint = https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/prod/
SearchInfraStack.DocumentsBucketName = ai-search-documents-123456789012
SearchInfraStack.LambdaFunctionName = ai-search-api
```

Save the **ApiEndpoint** - this is your API URL!

## Testing the Deployment

### 1. Health Check

```bash
curl https://YOUR-API-ENDPOINT/health/
```

Expected response:
```json
{"status": "ok"}
```

### 2. Upload a Document

```bash
curl -X POST "https://YOUR-API-ENDPOINT/documents/upload" \
  -F "file=@test.pdf"
```

### 3. Search

```bash
curl -X POST "https://YOUR-API-ENDPOINT/search/" \
  -H "Content-Type: application/json" \
  -d '{"query": "your search query", "top_k": 5}'
```

## Cost Monitoring

### Set Up Billing Alerts

1. Go to AWS Billing Console
2. Create a budget alert for $1/month
3. You'll get email notifications if costs exceed threshold

### Monitor Usage

```bash
# Check Lambda invocations
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=ai-search-api \
  --start-time 2025-01-01T00:00:00Z \
  --end-time 2025-01-31T23:59:59Z \
  --period 86400 \
  --statistics Sum

# Check DynamoDB usage
aws cloudwatch get-metric-statistics \
  --namespace AWS/DynamoDB \
  --metric-name ConsumedReadCapacityUnits \
  --dimensions Name=TableName,Value=ai-search-documents \
  --start-time 2025-01-01T00:00:00Z \
  --end-time 2025-01-31T23:59:59Z \
  --period 86400 \
  --statistics Sum
```

## Lambda Cold Start Optimization

### Current Strategy
1. **Pre-download model**: Sentence-transformers model is downloaded during Docker build
2. **FAISS in S3**: Index is loaded from S3 on cold start
3. **Memory allocation**: 3 GB ensures model fits in memory

### Expected Cold Start Times
- **First invocation**: 5-10 seconds (load model + FAISS index)
- **Warm invocations**: <100ms
- **Cold start frequency**: ~1 per 15 minutes of inactivity

### Optimization Tips
1. Use **Provisioned Concurrency** (costs money, but keeps 1 instance warm)
2. Implement **scheduled pings** to keep Lambda warm (CloudWatch Events)
3. Use **Lambda SnapStart** (not available for Docker images yet)

## Updating the Application

### Update Code Only

```bash
cd infra/cdk
cdk deploy
```

CDK will detect code changes, rebuild the Docker image, and update Lambda.

### Update Infrastructure

Modify `infra/cdk/lib/search-infra-stack.ts`, then:

```bash
cdk diff  # Preview changes
cdk deploy  # Apply changes
```

## Cleanup

To delete all resources and avoid any charges:

```bash
cd infra/cdk
cdk destroy
```

This will:
- Delete Lambda function
- Delete API Gateway
- Delete DynamoDB tables (data will be lost!)
- Delete S3 bucket and all files
- Delete CloudWatch logs

## Troubleshooting

### Lambda Timeout Errors

If you see timeout errors:
1. Check CloudWatch Logs: `aws logs tail /aws/lambda/ai-search-api --follow`
2. Increase timeout in CDK stack (max 900 seconds for Lambda, 29 seconds for API Gateway)
3. Optimize FAISS index loading

### Out of Memory Errors

If Lambda runs out of memory:
1. Increase `memorySize` in CDK stack (max 10,240 MB)
2. Reduce FAISS index size
3. Use smaller embedding model

### Docker Build Fails

If Docker build fails:
1. Ensure Docker is running
2. Check disk space (image is ~2-3 GB)
3. Try building locally: `cd services/search_api && docker build -f Dockerfile.lambda -t test .`

### API Gateway 502 Errors

If you get 502 Bad Gateway:
1. Check Lambda function logs
2. Verify Lambda has correct IAM permissions
3. Test Lambda directly: `aws lambda invoke --function-name ai-search-api response.json`

## Security Best Practices

1. **API Keys**: Add API Gateway API keys for production
2. **CORS**: Restrict allowed origins in production
3. **IAM**: Use least-privilege IAM roles
4. **Encryption**: Enable S3 bucket encryption
5. **VPC**: Deploy Lambda in VPC for private resources (costs extra)

## Next Steps

1. **Custom Domain**: Add Route 53 + CloudFront for custom domain
2. **CI/CD**: Set up GitHub Actions for automated deployments
3. **Monitoring**: Add X-Ray tracing for performance insights
4. **Caching**: Add CloudFront CDN for static responses
5. **Authentication**: Add Cognito for user authentication

## Free Tier Expiration Plan

After 12 months (or 6 months with new credit model):

**Option 1: Stay Serverless (Minimal Cost)**
- Lambda: ~$0.20/month for 50K requests
- API Gateway: ~$0.18/month for 50K requests
- DynamoDB: Free (Always Free tier)
- S3: ~$0.05/month for 2 GB
- **Total**: ~$0.43/month

**Option 2: Migrate to EC2 t4g.micro (ARM)**
- EC2: ~$6/month (24/7)
- More predictable costs
- Better for high-traffic applications

**Option 3: Shut Down**
- Run `cdk destroy` to delete all resources
- No ongoing costs
