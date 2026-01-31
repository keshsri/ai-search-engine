# CDK Infrastructure

AWS CDK infrastructure for the AI Semantic Search Engine.

## Architecture

- **DynamoDB**: 3 tables (documents, chunks, conversations)
- **S3**: Document storage + FAISS index
- **Lambda**: FastAPI application (Docker)
- **API Gateway**: REST API
- **CloudWatch**: Logs and alarms

## Prerequisites

- Node.js 18+
- npm
- AWS CLI configured
- AWS CDK installed globally

## Setup

```bash
# Install dependencies
npm install

# Bootstrap CDK (first time only)
cdk bootstrap

# Synthesize CloudFormation template
cdk synth

# Preview changes
cdk diff

# Deploy
cdk deploy

# Destroy
cdk destroy
```

## Project Structure

```
lib/
├── constructs/
│   ├── dynamodb-tables.ts    # DynamoDB tables
│   ├── storage-bucket.ts     # S3 bucket
│   ├── search-lambda.ts      # Lambda function
│   ├── api-gateway.ts        # API Gateway
│   └── monitoring.ts         # CloudWatch alarms
└── search-infra-stack.ts     # Main stack

bin/
└── cdk.ts                    # CDK app entry point

cdk.json                      # CDK configuration
```

## Stack Outputs

After deployment:

- `ApiEndpoint`: API Gateway URL
- `DocumentsTableName`: DynamoDB documents table
- `ChunksTableName`: DynamoDB chunks table
- `ConversationsTableName`: DynamoDB conversations table
- `DocumentsBucketName`: S3 bucket name
- `LambdaFunctionName`: Lambda function name

## Configuration

### DynamoDB Tables

- Billing: Pay-per-request (on-demand)
- Removal policy: DESTROY
- Point-in-time recovery: Disabled

### S3 Bucket

- Encryption: AES-256
- Lifecycle: 90-day expiration
- Public access: Blocked
- Versioning: Disabled

### Lambda

- Runtime: Python 3.12 (Docker)
- Memory: 3008 MB (3 GB)
- Timeout: 300 seconds (5 minutes)
- Ephemeral storage: 512 MB

### API Gateway

- Type: REST API
- Stage: dev
- Throttling: 100 req/s steady, 200 burst
- CORS: Enabled

### CloudWatch Alarms

- Lambda errors >10 in 5 minutes
- Lambda invocations >30K/day
- DynamoDB reads >6M/day
- API Gateway 5xx errors >5%

## Useful Commands

```bash
# List stacks
cdk list

# Synthesize template
cdk synth

# Compare deployed stack with current state
cdk diff

# Deploy stack
cdk deploy

# Destroy stack
cdk destroy

# View documentation
cdk docs
```

## Cost Optimization

- Serverless (no idle costs)
- Pay-per-request DynamoDB
- 7-day log retention
- S3 lifecycle policies
- No provisioned concurrency

## Security

- IAM roles (no static credentials)
- Least privilege permissions
- S3 encryption at rest
- DynamoDB encryption at rest
- HTTPS only (API Gateway)

## Troubleshooting

### Deployment Fails

Check:
- AWS credentials configured
- CDK bootstrapped
- Docker running (for Lambda image)
- Sufficient IAM permissions

### Stack Update Fails

```bash
# View CloudFormation events
aws cloudformation describe-stack-events --stack-name SearchInfraStack

# Check stack status
aws cloudformation describe-stacks --stack-name SearchInfraStack
```

### Resource Already Exists

If resources exist from previous deployment:
```bash
# Delete stack
cdk destroy

# Or manually delete via AWS Console
```

## Notes

- First deployment takes 10-15 minutes (Docker build)
- Subsequent deployments faster (~5 minutes)
- Stack name: `SearchInfraStack`
- Region: us-east-1 (configurable)
