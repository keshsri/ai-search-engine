# GitHub Actions Deployment

## Overview

Automated deployment using GitHub Actions with AWS IAM OIDC authentication (no static credentials).

**Benefits**:
- No long-lived credentials
- Automatic credential rotation
- More secure than access keys
- AWS best practice

## Setup Steps

### 1. Create IAM OIDC Provider

Run once in your AWS account:

```bash
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1
```

**Or via AWS Console**:
1. IAM → Identity providers → Add provider
2. Provider type: OpenID Connect
3. Provider URL: `https://token.actions.githubusercontent.com`
4. Audience: `sts.amazonaws.com`

### 2. Create IAM Role

**Get your information**:
```bash
# AWS Account ID
aws sts get-caller-identity --query Account --output text

# GitHub username and repo name
# Example: username/repo-name
```

**Create trust policy** (`github-trust-policy.json`):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:USERNAME/REPO:*"
        }
      }
    }
  ]
}
```

Replace `ACCOUNT_ID`, `USERNAME`, and `REPO` with your values.

**Create role**:

```bash
aws iam create-role \
  --role-name GitHubActionsDeployRole \
  --assume-role-policy-document file://github-trust-policy.json
```

### 3. Attach Permissions

**For personal projects**:

```bash
aws iam attach-role-policy \
  --role-name GitHubActionsDeployRole \
  --policy-arn arn:aws:iam::aws:policy/AdministratorAccess
```

**For production**: Create custom policy with only required permissions (CloudFormation, Lambda, API Gateway, S3, DynamoDB, IAM, ECR, CloudWatch).

### 4. Add Role ARN to GitHub Secrets

**Get role ARN**:
```bash
aws iam get-role --role-name GitHubActionsDeployRole --query Role.Arn --output text
```

**Add to GitHub**:
1. Repository → Settings → Secrets and variables → Actions
2. New repository secret
3. Name: `AWS_ROLE_ARN`
4. Value: Paste role ARN
5. Add secret

## Deploy

### Manual Deployment

1. Go to repository → Actions tab
2. Select "Deploy to AWS" workflow
3. Click "Run workflow"
4. Wait 15-20 minutes

### Automatic Deployment

Push to main branch triggers automatic deployment.

## Workflow

```yaml
1. Checkout code
2. Free up disk space
3. Setup Node.js + Python
4. Configure AWS credentials (OIDC)
5. Install CDK dependencies
6. CDK deploy
```

## Verify Deployment

Check workflow logs for:
- API Gateway endpoint URL
- Lambda function name
- S3 bucket name
- DynamoDB table names

**Test**:
```bash
curl https://YOUR-API-ENDPOINT/health/
```

## Troubleshooting

### "User not authorized to perform: sts:AssumeRoleWithWebIdentity"

**Fix**: Verify trust policy has correct GitHub username and repo name.

### "Access Denied" during deployment

**Fix**: Attach AdministratorAccess policy to role.

### "OIDC provider not found"

**Fix**: Run Step 1 to create OIDC provider.

### "No space left on device"

**Fix**: Workflow includes disk cleanup step. If still failing, reduce Docker image size.

## Cleanup

Delete all resources:

```bash
# Via AWS CLI
aws cloudformation delete-stack --stack-name SearchInfraStack

# Or via CDK locally
cd infra/cdk
cdk destroy
```

## Security

✅ No static credentials  
✅ OIDC authentication  
✅ Scoped to specific repository  
✅ No credentials in code

**Additional recommendations**:
- Use least privilege (custom policy vs. AdministratorAccess)
- Enable CloudTrail for audit logging
- Set up AWS Budgets for cost alerts
- Review IAM permissions regularly

## Cost Monitoring

After deployment:
1. AWS Billing Console → Free Tier usage
2. Set up budget alerts ($5/month threshold)
3. Monitor CloudWatch alarms

## Next Steps

1. Test API endpoints
2. Update application code
3. Push to main branch (auto-deploys)
4. Monitor costs and usage
