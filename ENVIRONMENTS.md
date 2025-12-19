# Environment Configuration Guide

This project supports **three environments**:

1. **dev** - Local development (not deployed to AWS)
2. **int** - Integration environment (deployed from `develop` branch)
3. **prod** - Production environment (deployed from `main` branch)

---

## Environment Structure

```
infrastructure/environments/
├── dev/          # Local development (not deployed)
├── int/          # Integration environment
└── prod/         # Production environment
```

Each environment has:
- `main.tf` - Terraform configuration
- `backend.tf` - Terraform state backend configuration
- `variables.tf` - Variable definitions
- `terraform.tfvars.example` - Example configuration file

---

## Deployment Flow

### Integration (int) Environment
- **Branch:** `develop`
- **Trigger:** Push to `develop` branch
- **Deploys:** Lambda functions, API Gateway, DynamoDB, S3, CloudFront
- **Purpose:** Pre-production testing and validation

### Production (prod) Environment
- **Branch:** `main`
- **Trigger:** Push to `main` branch
- **Deploys:** Lambda functions, API Gateway, DynamoDB, S3, CloudFront
- **Purpose:** Live production environment

---

## Setup Instructions

### 1. Integration Environment Setup

```bash
cd infrastructure/environments/int
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your integration values
```

**Required Variables:**
- `aws_region` - AWS region (default: us-east-1)
- `environment` - Set to "int"
- `project_name` - Project name (default: llm-duel-arena)
- `openai_api_key` - OpenAI API key (optional)
- `google_client_id` - Google OAuth client ID (optional)
- `google_client_secret` - Google OAuth client secret (optional)
- `domain_name` - Custom domain (optional, leave empty for default)

### 2. Production Environment Setup

```bash
cd infrastructure/environments/prod
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your production values
```

**Required Variables:** Same as integration, but use production values.

---

## CI/CD Configuration

### GitHub Actions Environments

You need to configure two GitHub environments:

1. **integration** - For `develop` branch deployments
2. **production** - For `main` branch deployments

### Setting Up GitHub Environments

1. Go to your repository → Settings → Environments
2. Create `integration` environment
3. Create `production` environment
4. Add required secrets to each environment:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`

### Deployment Secrets

Each environment should have its own AWS credentials:
- **Integration:** Use AWS credentials with permissions for integration resources
- **Production:** Use AWS credentials with permissions for production resources

---

## Manual Deployment

### Deploy Integration Environment

```bash
cd infrastructure
./deploy.sh int us-east-1
```

### Deploy Production Environment

```bash
cd infrastructure
./deploy.sh prod us-east-1
```

---

## Resource Naming

Resources are named with environment suffix:
- Integration: `llm-duel-arena-*-int`
- Production: `llm-duel-arena-*-prod`

Examples:
- Lambda: `llm-duel-arena-game-int`, `llm-duel-arena-game-prod`
- DynamoDB: `llm-duel-arena-users-int`, `llm-duel-arena-users-prod`
- S3: `llm-duel-arena-static-int`, `llm-duel-arena-static-prod`

---

## Terraform State

Each environment has its own Terraform state:
- Integration: `s3://llm-duel-arena-terraform-state/int/terraform.tfstate`
- Production: `s3://llm-duel-arena-terraform-state/prod/terraform.tfstate`

This ensures complete isolation between environments.

---

## Best Practices

1. **Always test in integration first** before deploying to production
2. **Use separate AWS accounts** or IAM roles for each environment
3. **Keep secrets separate** - don't share credentials between environments
4. **Monitor both environments** - set up CloudWatch alarms for both
5. **Document changes** - update this guide when adding new environments

---

## Troubleshooting

### Deployment fails with "environment not found"
- Ensure GitHub environment is created in repository settings
- Check that environment name matches exactly: `integration` or `production`

### Terraform state locked
- Check if another deployment is running
- Wait for previous deployment to complete
- If stuck, manually unlock: `terraform force-unlock <LOCK_ID>`

### Lambda deployment fails
- Check AWS credentials have Lambda permissions
- Verify Lambda package size is under 50MB (unzipped)
- Check CloudWatch logs for errors

---

## Next Steps

1. Configure `terraform.tfvars` for both `int` and `prod`
2. Set up GitHub environments with AWS credentials
3. Push to `develop` branch to deploy integration
4. Test integration environment
5. Merge to `main` to deploy production






