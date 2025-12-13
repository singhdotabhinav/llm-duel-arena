# 🚀 Quick CI/CD Setup Guide

**5-minute setup guide for GitHub Actions CI/CD**

## Prerequisites

- ✅ GitHub repository created
- ✅ AWS account with CLI configured
- ✅ Python 3.11+ installed

## Step 1: Run Setup Script (Easiest)

```bash
chmod +x setup-cicd.sh
./setup-cicd.sh
```

This script will:
- ✅ Check AWS CLI configuration
- ✅ Create IAM user for CI/CD
- ✅ Generate access keys
- ✅ Guide you through GitHub setup

## Step 2: Manual Setup (Alternative)

### 2.1 Create AWS IAM User

```bash
# Create IAM user
aws iam create-user --user-name llm-duel-arena-cicd

# Create access key
aws iam create-access-key --user-name llm-duel-arena-cicd

# Attach policies
aws iam attach-user-policy --user-name llm-duel-arena-cicd --policy-arn arn:aws:iam::aws:policy/AWSLambda_FullAccess
aws iam attach-user-policy --user-name llm-duel-arena-cicd --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess
aws iam attach-user-policy --user-name llm-duel-arena-cicd --policy-arn arn:aws:iam::aws:policy/CloudFrontFullAccess
aws iam attach-user-policy --user-name llm-duel-arena-cicd --policy-arn arn:aws:iam::aws:policy/AmazonAPIGatewayAdministrator
aws iam attach-user-policy --user-name llm-duel-arena-cicd --policy-arn arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess
```

**Save the Access Key ID and Secret Access Key!**

### 2.2 Add GitHub Secrets

1. Go to: `https://github.com/YOUR_USERNAME/llm-duel-arena/settings/secrets/actions`
2. Click **"New repository secret"**
3. Add these secrets:

| Secret Name | Value |
|------------|-------|
| `AWS_ACCESS_KEY_ID` | From Step 2.1 |
| `AWS_SECRET_ACCESS_KEY` | From Step 2.1 |

### 2.3 Create GitHub Environments

1. Go to: `https://github.com/YOUR_USERNAME/llm-duel-arena/settings/environments`
2. Click **"New environment"**
3. Create **"development"**:
   - Name: `development`
   - Deployment branches: `develop`
4. Create **"production"**:
   - Name: `production`
   - Deployment branches: `main`
   - ✅ **Add protection rules** (recommended):
     - Required reviewers: 1
     - Wait timer: 5 minutes (optional)

## Step 3: Test the Pipeline

```bash
# Create test branch
git checkout -b test-ci-cd

# Make a small change
echo "# Test CI/CD" >> README.md
git add README.md
git commit -m "Test CI/CD pipeline"
git push origin test-ci-cd

# Create PR to 'develop' branch
# Check Actions tab to see workflow run
```

## Step 4: Verify Setup

### Check GitHub Actions

1. Go to: `https://github.com/YOUR_USERNAME/llm-duel-arena/actions`
2. You should see:
   - ✅ **Test Suite** workflow (runs on every push/PR)
   - ✅ **CI/CD Pipeline** workflow (runs on push to main/develop)

### Check Workflow Status

- Green checkmark ✅ = Success
- Red X ❌ = Failed (check logs)
- Yellow circle ⏳ = Running

## Troubleshooting

### ❌ "AWS credentials not configured"

**Fix:**
```bash
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Enter default region (e.g., us-east-1)
```

### ❌ "The security token included in the request is invalid"

**Fix:** 
- Verify GitHub Secrets are set correctly
- Check IAM user has correct permissions
- Ensure access keys are active

### ❌ "Terraform backend error"

**Fix:**
```bash
cd infrastructure
./setup-state-bucket.sh us-east-1
```

### ❌ "Lambda function not found"

**Fix:**
- Deploy infrastructure first: `terraform apply`
- Check function names match in Terraform config

## What Happens When You Push?

### Push to `develop` branch:
1. ✅ Run tests
2. ✅ Build Lambda packages
3. ✅ Deploy to **development** environment
4. ✅ Run integration tests

### Push to `main` branch:
1. ✅ Run tests
2. ✅ Build Lambda packages
3. ✅ Deploy to **production** environment (may require approval)
4. ✅ Run integration tests

### Push to other branches:
1. ✅ Run tests only (no deployment)

## Next Steps

1. ✅ CI/CD is set up
2. 📋 Review `DEPLOYMENT_ROADMAP.md` for full deployment guide
3. 🔧 Fix Phase 1 issues (session cookie, database migration)
4. 🚀 Deploy to production!

## Quick Reference

| Task | Command |
|------|---------|
| Setup CI/CD | `./setup-cicd.sh` |
| Test pipeline | Create PR to `develop` |
| View logs | GitHub → Actions tab |
| Manual deploy | `cd infrastructure && ./deploy.sh prod us-east-1` |

---

**Need help?** Check `CI_CD_SETUP.md` for detailed documentation.

