# Complete Deployment Guide

This guide covers deploying LLM Duel Arena to AWS using the serverless architecture.

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **AWS CLI** installed and configured (`aws configure`)
3. **Terraform** >= 1.0 installed
4. **Python** 3.11+ for building Lambda packages

## Step 1: Initial Setup (One-Time)

### 1.1 Create Terraform State Backend

Before deploying, create the S3 bucket and DynamoDB table for Terraform state:

```bash
cd infrastructure
./setup-state-bucket.sh us-east-1
```

This creates:
- S3 bucket: `llm-duel-arena-terraform-state`
- DynamoDB table: `llm-duel-arena-terraform-locks`

### 1.2 Configure Environment Variables

Choose an environment (dev or prod) and configure:

```bash
cd infrastructure/environments/dev  # or prod
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars`:

```hcl
aws_region  = "us-east-1"
environment = "dev"
project_name = "llm-duel-arena"

openai_api_key       = "sk-your-key-here"
google_client_id     = "your-client-id.apps.googleusercontent.com"
google_client_secret = "your-client-secret"

domain_name = ""  # Optional: custom domain
```

## Step 2: Deploy Infrastructure

### 2.1 Initialize Terraform

```bash
cd infrastructure/environments/dev
terraform init
```

This will:
- Download AWS provider
- Configure S3 backend for state storage

### 2.2 Review Deployment Plan

```bash
terraform plan -var-file=terraform.tfvars
```

Review the resources that will be created:
- Lambda functions (game, auth, LLM)
- API Gateway HTTP API
- DynamoDB tables
- S3 buckets
- CloudFront distribution
- IAM roles and policies
- Secrets Manager secrets

### 2.3 Deploy Infrastructure

```bash
terraform apply -var-file=terraform.tfvars
```

Type `yes` when prompted. This takes 5-10 minutes.

### 2.4 Get Deployment Outputs

```bash
terraform output
```

Save these values:
- `api_gateway_url`: Your API endpoint
- `cloudfront_url`: Your frontend URL
- `s3_bucket_name`: Static assets bucket
- `cloudfront_distribution_id`: For cache invalidation

## Step 3: Build and Deploy Lambda Functions

### 3.1 Build Lambda Packages

From the infrastructure root:

```bash
cd infrastructure
./build-lambda.sh dev  # or prod
```

This creates deployment packages in `infrastructure/deployments/`:
- `game.zip`
- `auth.zip`
- `llm.zip`

### 3.2 Deploy Lambda Functions

The deployment script handles this automatically:

```bash
./deploy.sh dev us-east-1
```

Or manually update each function:

```bash
aws lambda update-function-code \
  --function-name llm-duel-arena-game-dev \
  --zip-file fileb://deployments/game.zip \
  --region us-east-1

aws lambda update-function-code \
  --function-name llm-duel-arena-auth-dev \
  --zip-file fileb://deployments/auth.zip \
  --region us-east-1

aws lambda update-function-code \
  --function-name llm-duel-arena-llm-dev \
  --zip-file fileb://deployments/llm.zip \
  --region us-east-1
```

## Step 4: Deploy Static Assets

### 4.1 Upload to S3

```bash
cd infrastructure
./deploy-static.sh dev us-east-1
```

This script:
1. Uploads `app/static/` to S3
2. Uploads `app/templates/` to S3
3. Invalidates CloudFront cache

### 4.2 Manual Upload (Alternative)

```bash
# Get bucket name from Terraform output
BUCKET=$(cd environments/dev && terraform output -raw s3_bucket_name)

# Upload static files
aws s3 sync app/static/ s3://${BUCKET}/static/ --delete

# Upload templates
aws s3 sync app/templates/ s3://${BUCKET}/ --delete

# Invalidate CloudFront
DIST_ID=$(cd environments/dev && terraform output -raw cloudfront_distribution_id)
aws cloudfront create-invalidation --distribution-id ${DIST_ID} --paths "/*"
```

## Step 5: Configure Frontend for AWS

### 5.1 Update API Gateway URL

The frontend automatically detects local vs AWS deployment. For production, you may need to set the API Gateway URL:

1. Get API Gateway URL:
   ```bash
   cd infrastructure/environments/dev
   terraform output api_gateway_url
   ```

2. Add to your HTML templates (or use environment variable):
   ```html
   <meta name="api-gateway-url" content="https://your-api-id.execute-api.us-east-1.amazonaws.com">
   ```

### 5.2 Update Google OAuth Redirect URI

Update your Google OAuth credentials to include the CloudFront URL:

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Edit your OAuth 2.0 Client ID
3. Add authorized redirect URI: `https://your-cloudfront-url.cloudfront.net/auth/callback`
4. Update `GOOGLE_REDIRECT_URI` in Secrets Manager or redeploy

## Step 6: Test Deployment

### 6.1 Test API Endpoints

```bash
# Get API Gateway URL
API_URL=$(cd infrastructure/environments/dev && terraform output -raw api_gateway_url)

# Test health endpoint (if you have one)
curl ${API_URL}/api/games/health

# Test game creation
curl -X POST ${API_URL}/api/games/create \
  -H "Content-Type: application/json" \
  -d '{"game_type": "chess", "white_model": "ollama:llama3.1:latest", "black_model": "ollama:mistral-nemo:latest"}'
```

### 6.2 Test Frontend

1. Visit CloudFront URL from Terraform output
2. Test game creation
3. Test authentication
4. Check browser console for errors

### 6.3 Monitor Logs

```bash
# View Lambda logs
aws logs tail /aws/lambda/llm-duel-arena-game-dev --follow

# View API Gateway logs
aws logs tail /aws/apigateway/llm-duel-arena-api-dev --follow
```

## Step 7: CI/CD Setup (Optional)

### 7.1 Configure GitHub Secrets

Add these secrets to your GitHub repository:

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `OPENAI_API_KEY`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`

### 7.2 Push to Trigger Deployment

The workflow automatically:
- Runs tests
- Deploys infrastructure
- Builds and updates Lambda functions
- Deploys static assets

```bash
git push origin main  # Deploys to prod
git push origin develop  # Deploys to dev
```

## Local Development

The application still supports local development with FastAPI:

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
uvicorn app.main:app --reload
```

The frontend automatically detects localhost and uses `http://localhost:8000` for API calls.

## Troubleshooting

### Lambda Function Not Found

- Ensure Terraform applied successfully
- Check function names match in `modules/core/lambda.tf`
- Verify IAM permissions

### DynamoDB Access Denied

- Check IAM role policies in `modules/core/iam.tf`
- Verify table names match

### API Gateway Returns 500

- Check CloudWatch logs: `aws logs tail /aws/lambda/llm-duel-arena-game-dev --follow`
- Verify environment variables are set
- Check Secrets Manager permissions

### CORS Errors

- Update CORS configuration in `modules/core/api_gateway.tf`
- Add your domain to allowed origins

### Static Assets Not Loading

- Verify S3 bucket policy allows CloudFront access
- Check CloudFront distribution origin settings
- Invalidate CloudFront cache

## Cost Monitoring

Set up billing alerts:

```bash
aws budgets create-budget \
  --account-id $(aws sts get-caller-identity --query Account --output text) \
  --budget file://budget.json
```

Expected costs:
- **Low traffic** (500 games/month): $0.60-1.00
- **Medium traffic** (5,000 games/month): $1.50-5.50
- **High traffic** (50,000 games/month): $10.50-32.50

## Cleanup

To destroy all resources:

```bash
cd infrastructure/environments/dev
terraform destroy -var-file=terraform.tfvars
```

**Warning**: This deletes all data in DynamoDB!

## Next Steps

1. ✅ Infrastructure deployed
2. ⏳ Test all endpoints
3. ⏳ Set up monitoring and alerts
4. ⏳ Configure custom domain (optional)
5. ⏳ Set up backup strategy for DynamoDB
6. ⏳ Implement rate limiting
7. ⏳ Add API authentication

---

**Status**: ✅ Ready for deployment

**Estimated deployment time**: 30-60 minutes (first time)











