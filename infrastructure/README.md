# LLM Duel Arena - Infrastructure as Code

This directory contains Terraform configuration for deploying the LLM Duel Arena to AWS using **serverless architecture** (Lambda + API Gateway + DynamoDB).

## Architecture

- **Lambda**: Serverless compute (game, auth, LLM services)
- **API Gateway**: HTTP API for routing
- **DynamoDB**: NoSQL database (pay-per-request)
- **S3 + CloudFront**: Static asset hosting
- **Secrets Manager**: Secure storage for API keys

## Cost

Expected monthly cost: **$1-5** (with free tier)

- Lambda: Free tier (1M requests/month)
- API Gateway: Free tier (1M requests/month)
- DynamoDB: Free tier (25 GB storage, 25 RCU/WCU)
- CloudFront: Free tier (50 GB transfer/month)
- S3: Free tier (5 GB storage)

## Prerequisites

1. AWS CLI configured with credentials
2. Terraform >= 1.0 installed
3. AWS account with appropriate permissions

## Quick Start

1. **Copy example variables:**
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   ```

2. **Edit terraform.tfvars with your values:**
   ```bash
   aws_region = "us-east-1"
   environment = "dev"
   openai_api_key = "sk-..."
   google_client_id = "..."
   google_client_secret = "..."
   ```

3. **Deploy:**
   ```bash
   ./deploy.sh dev us-east-1
   ```

## Manual Deployment

1. **Initialize Terraform:**
   ```bash
   terraform init
   ```

2. **Plan deployment:**
   ```bash
   terraform plan -var-file=terraform.tfvars
   ```

3. **Deploy:**
   ```bash
   terraform apply -var-file=terraform.tfvars
   ```

## CI/CD

GitHub Actions workflow automatically deploys on push to `main` branch.

Required GitHub Secrets:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `OPENAI_API_KEY`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`

## Outputs

After deployment, get your endpoints:

```bash
terraform output api_gateway_url
terraform output cloudfront_url
```

## Destroy

To tear down all resources:

```bash
terraform destroy -var-file=terraform.tfvars
```

## Structure

- `main.tf`: Provider and core configuration
- `variables.tf`: Input variables
- `outputs.tf`: Output values
- `lambda.tf`: Lambda function definitions
- `api_gateway.tf`: API Gateway configuration
- `dynamodb.tf`: DynamoDB tables
- `s3.tf`: S3 buckets
- `cloudfront.tf`: CloudFront distribution
- `iam.tf`: IAM roles and policies
- `secrets.tf`: Secrets Manager configuration
- `deploy.sh`: Deployment script
