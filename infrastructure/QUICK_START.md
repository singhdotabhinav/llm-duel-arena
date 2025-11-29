# Quick Start: Deploy LLM Duel Arena to AWS

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **AWS CLI** installed and configured
3. **Terraform** >= 1.0 installed
4. **Python** 3.11+ for building Lambda packages

> **Note:** Run Terraform commands from `infrastructure/environments/<env>` (dev or prod).

## Step 1: Configure AWS

```bash
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key  
# Default region: us-east-1
# Default output: json
```

## Step 2: Set Up Terraform Variables

```bash
cd infrastructure/environments/dev   # or environments/prod
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars`:
```hcl
aws_region  = "us-east-1"
environment = "dev"
project_name = "llm-duel-arena"

openai_api_key      = "sk-your-key-here"
google_client_id    = "your-client-id.apps.googleusercontent.com"
google_client_secret = "your-client-secret"
```

## Step 3: Initialize Terraform

```bash
terraform init
```

## Step 4: Review Plan

```bash
terraform plan -var-file=terraform.tfvars
```

Review the changes that will be created.

## Step 5: Deploy

```bash
terraform apply -var-file=terraform.tfvars
```

Type `yes` when prompted.

## Step 6: Get Endpoints

After deployment, get your API endpoints:

```bash
terraform output api_gateway_url
terraform output cloudfront_url
```

## Step 7: Build and Deploy Lambda Functions

```bash
# Build Lambda packages
cd ..
./deploy.sh dev us-east-1

# Or manually:
mkdir -p deployments
cd ../app
zip -r ../infrastructure/deployments/game.zip services/ lambda_handlers/game_handler.py -x "*.pyc" "__pycache__/*"
zip -r ../infrastructure/deployments/auth.zip routers/auth.py lambda_handlers/auth_handler.py -x "*.pyc" "__pycache__/*"
zip -r ../infrastructure/deployments/llm.zip models/ lambda_handlers/llm_handler.py -x "*.pyc" "__pycache__/*"

# Update Lambda functions
cd ../infrastructure
aws lambda update-function-code \
  --function-name llm-duel-arena-game-dev \
  --zip-file fileb://deployments/game.zip

aws lambda update-function-code \
  --function-name llm-duel-arena-auth-dev \
  --zip-file fileb://deployments/auth.zip

aws lambda update-function-code \
  --function-name llm-duel-arena-llm-dev \
  --zip-file fileb://deployments/llm.zip
```

## Step 8: Deploy Static Assets

```bash
# Build frontend (if you have a build process)
# npm run build

# Upload to S3
aws s3 sync app/static/ s3://llm-duel-arena-static-dev-ACCOUNT_ID/static/
aws s3 sync app/templates/ s3://llm-duel-arena-static-dev-ACCOUNT_ID/

# Invalidate CloudFront cache
cd infrastructure/environments/dev
aws cloudfront create-invalidation \
  --distribution-id $(terraform output -raw cloudfront_distribution_id) \
  --paths "/*"
```

## Step 9: Test

1. Visit CloudFront URL from Step 6
2. Test game creation
3. Test authentication
4. Monitor CloudWatch logs

## Troubleshooting

### Lambda function not found
- Make sure Terraform applied successfully
- Check function names match in `lambda.tf`

### DynamoDB table not found
- Check table name in `dynamodb.tf`
- Verify IAM permissions

### API Gateway returns 500
- Check CloudWatch logs for Lambda errors
- Verify environment variables are set
- Check Secrets Manager permissions

### CORS errors
- Update `api_gateway.tf` CORS configuration
- Add your domain to allowed origins

## Cost Monitoring

Set up billing alerts:
```bash
aws budgets create-budget \
  --account-id $(aws sts get-caller-identity --query Account --output text) \
  --budget file://budget.json
```

Create `budget.json`:
```json
{
  "BudgetName": "llm-duel-arena-monthly",
  "BudgetLimit": {
    "Amount": "10",
    "Unit": "USD"
  },
  "TimeUnit": "MONTHLY",
  "BudgetType": "COST"
}
```

## Next Steps

1. ✅ Infrastructure deployed
2. ⏳ Test all endpoints
3. ⏳ Migrate existing data
4. ⏳ Update frontend
5. ⏳ Set up CI/CD
6. ⏳ Monitor costs

## Cleanup

To destroy all resources:

```bash
cd infrastructure/environments/dev
terraform destroy -var-file=terraform.tfvars
```

**Warning**: This will delete all data in DynamoDB!








