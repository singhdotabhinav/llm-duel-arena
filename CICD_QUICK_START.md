# 🚀 CI/CD Quick Start - 5 Minutes

Get your CI/CD pipeline running in 5 minutes!

## Option 1: Automated Setup (Recommended)

```bash
# Run the setup script
./setup-cicd.sh
```

Follow the prompts. The script will:
- ✅ Check AWS CLI configuration
- ✅ Create IAM user for CI/CD
- ✅ Generate access keys
- ✅ Guide you through GitHub setup

## Option 2: Manual Setup

### Step 1: Create AWS IAM User (2 minutes)

```bash
# Create user
aws iam create-user --user-name llm-duel-arena-cicd

# Create access key (save the output!)
aws iam create-access-key --user-name llm-duel-arena-cicd

# Attach policies
aws iam attach-user-policy --user-name llm-duel-arena-cicd --policy-arn arn:aws:iam::aws:policy/AWSLambda_FullAccess
aws iam attach-user-policy --user-name llm-duel-arena-cicd --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess
aws iam attach-user-policy --user-name llm-duel-arena-cicd --policy-arn arn:aws:iam::aws:policy/CloudFrontFullAccess
aws iam attach-user-policy --user-name llm-duel-arena-cicd --policy-arn arn:aws:iam::aws:policy/AmazonAPIGatewayAdministrator
aws iam attach-user-policy --user-name llm-duel-arena-cicd --policy-arn arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess
```

### Step 2: Add GitHub Secrets (1 minute)

1. Go to: `https://github.com/YOUR_USERNAME/llm-duel-arena/settings/secrets/actions`
2. Click **"New repository secret"**
3. Add:
   - Name: `AWS_ACCESS_KEY_ID` → Value: (from Step 1)
   - Name: `AWS_SECRET_ACCESS_KEY` → Value: (from Step 1)

### Step 3: Create Environments (1 minute)

1. Go to: `https://github.com/YOUR_USERNAME/llm-duel-arena/settings/environments`
2. Click **"New environment"**
3. Create:
   - **development** (deployment branches: `develop`)
   - **production** (deployment branches: `main`)

### Step 4: Test (1 minute)

```bash
git checkout -b test-ci-cd
echo "# Test" >> README.md
git add README.md
git commit -m "Test CI/CD"
git push origin test-ci-cd
```

Create PR to `develop` → Check Actions tab ✅

## What You Get

✅ **Automated Testing** - Runs on every push/PR  
✅ **Automated Deployment** - Deploys on push to main/develop  
✅ **Multi-Environment** - Separate dev and prod deployments  
✅ **Infrastructure as Code** - Terraform automation  
✅ **Lambda Deployment** - Automatic function updates  
✅ **Static Assets** - S3 + CloudFront deployment  

## Workflow Files

- `.github/workflows/test.yml` - Test suite (runs on every push)
- `.github/workflows/ci-cd.yml` - Full CI/CD pipeline (runs on main/develop)

## Next Steps

1. ✅ CI/CD is set up
2. 📋 Review `DEPLOYMENT_ROADMAP.md`
3. 🔧 Fix Phase 1 issues (session cookie, database migration)
4. 🚀 Deploy!

---

**Need help?** See `CI_CD_SETUP.md` for detailed docs.

