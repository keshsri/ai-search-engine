# GitHub Actions Deployment Setup (IAM Role with OIDC)

## Overview

This setup uses AWS IAM roles with OIDC (OpenID Connect) for secure, keyless authentication from GitHub Actions.

**Benefits:**
- No long-lived credentials
- Automatic credential rotation
- More secure than access keys
- AWS best practice

## Setup Steps

### Step 1: Create IAM OIDC Provider

Run this command once in your AWS account:

```bash
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1
```

**Or via AWS Console:**
1. Go to IAM → Identity providers → Add provider
2. Provider type: OpenID Connect
3. Provider URL: `https://token.actions.githubusercontent.com`
4. Audience: `sts.amazonaws.com`
5. Click "Add provider"

### Step 2: Create IAM Role

**Get your information:**
- AWS Account ID: Run `aws sts get-caller-identity --query Account --output text`
- GitHub username: Your GitHub username
- Repository name: Your repository name (e.g., `ai-search-engine`)

**Create trust policy file** (`github-trust-policy.json`):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::YOUR_ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:YOUR_GITHUB_USERNAME/YOUR_REPO_NAME:*"
        }
      }
    }
  ]
}
```

**Replace:**
- `YOUR_ACCOUNT_ID` → Your AWS account ID
- `YOUR_GITHUB_USERNAME` → Your GitHub username
- `YOUR_REPO_NAME` → Your repository name

**Create the role:**

```bash
aws iam create-role \
  --role-name GitHubActionsDeployRole \
  --assume-role-policy-document file://github-trust-policy.json \
  --description "Role for GitHub Actions to deploy CDK stacks"
```

### Step 3: Attach Permissions to Role

**For simplicity (personal project):**

```bash
aws iam attach-role-policy \
  --role-name GitHubActionsDeployRole \
  --policy-arn arn:aws:iam::aws:policy/AdministratorAccess
```

**For production (more secure):**

Create a custom policy with only CDK permissions:
- CloudFormation (create/update/delete stacks)
- Lambda (create/update functions)
- API Gateway (create/update APIs)
- S3 (create/manage buckets)
- DynamoDB (create/manage tables)
- IAM (create/manage roles)
- ECR (push Docker images)
- CloudWatch (create logs/alarms)

### Step 4: Add Role ARN to GitHub Secrets

1. **Get the role ARN:**
   ```bash
   aws iam get-role --role-name GitHubActionsDeployRole --query Role.Arn --output text
   ```
   
   Output will be: `arn:aws:iam::YOUR_ACCOUNT_ID:role/GitHubActionsDeployRole`

2. **Add to GitHub:**
   - Go to your GitHub repository
   - Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `AWS_ROLE_ARN`
   - Value: Paste the role ARN from step 1
   - Click "Add secret"

## Deploy

### Manual Deployment

1. Push your code to GitHub (if not already done)
2. Go to your GitHub repository
3. Click "Actions" tab
4. Select "Deploy to AWS" workflow
5. Click "Run workflow" button
6. Click "Run workflow" to confirm
7. Wait 15-20 minutes for deployment

### Monitor Deployment

- Watch the workflow run in the Actions tab
- Deployment takes 15-20 minutes (Docker build + upload)
- Check the logs for any errors
- Look for outputs at the end (API endpoint, etc.)

## Verify Deployment

After successful deployment, check the workflow logs for:
- ✅ API Gateway endpoint URL
- ✅ Lambda function name
- ✅ S3 bucket name
- ✅ DynamoDB table names

**Test the API:**
```bash
curl https://YOUR-API-ENDPOINT/health/
```

## Troubleshooting

### Error: "User is not authorized to perform: sts:AssumeRoleWithWebIdentity"

**Cause:** Trust policy doesn't match your GitHub repo

**Fix:** Verify the trust policy has correct:
- GitHub username
- Repository name
- Format: `repo:username/repo-name:*`

### Error: "Access Denied" during deployment

**Cause:** Role doesn't have sufficient permissions

**Fix:** Attach AdministratorAccess policy (or create custom policy with required permissions)

### Error: "OIDC provider not found"

**Cause:** OIDC provider not created in AWS

**Fix:** Run Step 1 again to create the OIDC provider

### Error: "No space left on device" during Docker build

**Cause:** GitHub Actions runner out of disk space

**Fix:** This is rare, but if it happens:
- Reduce Docker image size
- Remove unnecessary dependencies
- Use multi-stage Docker build

## Clean Up

To delete all AWS resources:

**Option 1: Via AWS CLI**
```bash
aws cloudformation delete-stack --stack-name SearchInfraStack
```

**Option 2: Via CDK locally (if you have AWS CLI configured)**
```bash
cd infra/cdk
cdk destroy
```

**Option 3: Via AWS Console**
1. Go to CloudFormation console
2. Select `SearchInfraStack`
3. Click "Delete"

## Security Best Practices

✅ **Using IAM roles (no long-lived credentials)**
✅ **OIDC authentication (keyless)**
✅ **Scoped to specific GitHub repository**
✅ **No credentials in code or git**

**Additional recommendations:**
- Review IAM permissions regularly
- Use least privilege (custom policy instead of AdministratorAccess)
- Enable CloudTrail for audit logging
- Set up AWS Budgets for cost alerts

## Cost Monitoring

After deployment:
1. Go to AWS Billing Console
2. Check "Free Tier" usage
3. Set up budget alerts ($1/month threshold)
4. Monitor CloudWatch alarms in AWS Console

## Next Steps

After successful deployment:
1. Test the API endpoints
2. Update application code for S3 integration (FAISS index, file storage)
3. Redeploy with updated code
4. Monitor costs and usage
