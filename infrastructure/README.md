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

1. **Choose an environment (dev/prod):**
   ```bash
   cd environments/dev   # or environments/prod
   cp terraform.tfvars.example terraform.tfvars
   ```

2. **Edit `terraform.tfvars`:**
   ```hcl
   aws_region          = "us-east-1"
   project_name        = "llm-duel-arena"
   openai_api_key       = "sk-..."
   google_client_id     = "..."
   google_client_secret = "..."
   ```

3. **Deploy from the infrastructure root:**
   ```bash
   cd ..
   ./deploy.sh dev us-east-1
   ```

## Manual Deployment

```bash
cd environments/dev        # or environments/prod
terraform init
terraform plan -var-file=terraform.tfvars
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

```bash
cd environments/dev
terraform output api_gateway_url
terraform output cloudfront_url
```

## Destroy

```bash
cd environments/dev
terraform destroy -var-file=terraform.tfvars
```

## Structure

```
infrastructure/
├── modules/
│   └── core/                  # All shared AWS resources
├── environments/
│   ├── dev/                   # Dev backend + tfvars
│   └── prod/                  # Prod backend + tfvars
├── deploy.sh                  # Helper script (wraps env terraform)
├── build-lambda.sh            # Builds Lambda packages
├── QUICK_START.md             # Detailed guide
└── README.md                  # This file
```
