#!/bin/bash

# CI/CD Setup Helper Script
# This script helps you set up CI/CD for LLM Duel Arena

set -e

echo "🚀 LLM Duel Arena - CI/CD Setup Helper"
echo "========================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI is not installed${NC}"
    echo "Install it from: https://aws.amazon.com/cli/"
    exit 1
fi

echo -e "${GREEN}✅ AWS CLI found${NC}"

# Check if AWS credentials are configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ AWS credentials not configured${NC}"
    echo "Run: aws configure"
    exit 1
fi

echo -e "${GREEN}✅ AWS credentials configured${NC}"

# Get AWS account info
AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=$(aws configure get region || echo "us-east-1")

echo ""
echo -e "${BLUE}Current AWS Configuration:${NC}"
echo "  Account ID: $AWS_ACCOUNT"
echo "  Region: $AWS_REGION"
echo ""

# Check if GitHub CLI is installed (optional)
if command -v gh &> /dev/null; then
    echo -e "${GREEN}✅ GitHub CLI found${NC}"
    USE_GH_CLI=true
else
    echo -e "${YELLOW}⚠️  GitHub CLI not found (optional)${NC}"
    echo "  Install for easier secret management: https://cli.github.com/"
    USE_GH_CLI=false
fi

echo ""
echo "=========================================="
echo "Step 1: Create IAM User for CI/CD"
echo "=========================================="
echo ""

read -p "Do you want to create an IAM user for CI/CD? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    IAM_USER_NAME="llm-duel-arena-cicd"
    
    echo "Creating IAM user: $IAM_USER_NAME"
    
    # Check if user already exists
    if aws iam get-user --user-name "$IAM_USER_NAME" &> /dev/null; then
        echo -e "${YELLOW}⚠️  User $IAM_USER_NAME already exists${NC}"
        read -p "Do you want to create new access keys? (y/n) " -n 1 -r
        echo ""
        CREATE_KEYS=$REPLY
    else
        # Create user
        aws iam create-user --user-name "$IAM_USER_NAME"
        echo -e "${GREEN}✅ Created IAM user: $IAM_USER_NAME${NC}"
        CREATE_KEYS="y"
    fi
    
    if [[ $CREATE_KEYS =~ ^[Yy]$ ]]; then
        # Create access key
        echo "Creating access key..."
        ACCESS_KEY_OUTPUT=$(aws iam create-access-key --user-name "$IAM_USER_NAME")
        
        ACCESS_KEY_ID=$(echo $ACCESS_KEY_OUTPUT | jq -r '.AccessKey.AccessKeyId')
        SECRET_ACCESS_KEY=$(echo $ACCESS_KEY_OUTPUT | jq -r '.AccessKey.SecretAccessKey')
        
        echo ""
        echo -e "${GREEN}✅ Access Key Created${NC}"
        echo ""
        echo -e "${YELLOW}⚠️  IMPORTANT: Save these credentials securely!${NC}"
        echo "  Access Key ID: $ACCESS_KEY_ID"
        echo "  Secret Access Key: $SECRET_ACCESS_KEY"
        echo ""
        
        # Attach policies
        echo "Attaching policies..."
        aws iam attach-user-policy --user-name "$IAM_USER_NAME" --policy-arn arn:aws:iam::aws:policy/AWSLambda_FullAccess
        aws iam attach-user-policy --user-name "$IAM_USER_NAME" --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess
        aws iam attach-user-policy --user-name "$IAM_USER_NAME" --policy-arn arn:aws:iam::aws:policy/CloudFrontFullAccess
        aws iam attach-user-policy --user-name "$IAM_USER_NAME" --policy-arn arn:aws:iam::aws:policy/AmazonAPIGatewayAdministrator
        aws iam attach-user-policy --user-name "$IAM_USER_NAME" --policy-arn arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess
        aws iam attach-user-policy --user-name "$IAM_USER_NAME" --policy-arn arn:aws:iam::aws:policy/IAMFullAccess
        
        echo -e "${GREEN}✅ Policies attached${NC}"
        
        # Save to file (with warning)
        echo ""
        read -p "Save credentials to .github-secrets.txt? (y/n) " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            cat > .github-secrets.txt << EOF
# GitHub Secrets - Add these to your repository
# Repository → Settings → Secrets and variables → Actions → New repository secret

AWS_ACCESS_KEY_ID=$ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY=$SECRET_ACCESS_KEY

# Optional (if using SAM deployment):
# HUGGINGFACE_API_TOKEN=your_token_here
# APP_SECRET_KEY=your_secret_key_here
EOF
            chmod 600 .github-secrets.txt
            echo -e "${GREEN}✅ Saved to .github-secrets.txt${NC}"
            echo -e "${RED}⚠️  Keep this file secure and never commit it!${NC}"
        fi
    fi
fi

echo ""
echo "=========================================="
echo "Step 2: Set Up GitHub Secrets"
echo "=========================================="
echo ""

if [ -f .github-secrets.txt ]; then
    echo "Found .github-secrets.txt file"
    echo ""
    echo "To add secrets to GitHub:"
    echo "1. Go to: https://github.com/YOUR_USERNAME/llm-duel-arena/settings/secrets/actions"
    echo "2. Click 'New repository secret'"
    echo "3. Add each secret from the file below:"
    echo ""
    cat .github-secrets.txt
    echo ""
    
    if [ "$USE_GH_CLI" = true ]; then
        read -p "Do you want to add secrets using GitHub CLI? (y/n) " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            source .github-secrets.txt
            gh secret set AWS_ACCESS_KEY_ID --body "$AWS_ACCESS_KEY_ID"
            gh secret set AWS_SECRET_ACCESS_KEY --body "$AWS_SECRET_ACCESS_KEY"
            echo -e "${GREEN}✅ Secrets added to GitHub${NC}"
        fi
    fi
else
    echo "To add secrets manually:"
    echo "1. Go to: https://github.com/YOUR_USERNAME/llm-duel-arena/settings/secrets/actions"
    echo "2. Click 'New repository secret'"
    echo "3. Add these secrets:"
    echo "   - AWS_ACCESS_KEY_ID"
    echo "   - AWS_SECRET_ACCESS_KEY"
    echo ""
fi

echo ""
echo "=========================================="
echo "Step 3: Set Up GitHub Environments"
echo "=========================================="
echo ""

echo "To create environments:"
echo "1. Go to: https://github.com/YOUR_USERNAME/llm-duel-arena/settings/environments"
echo "2. Click 'New environment'"
echo "3. Create 'development' environment"
echo "   - Deployment branches: develop"
echo "4. Create 'production' environment"
echo "   - Deployment branches: main"
echo "   - Add protection rules (optional but recommended)"
echo ""

if [ "$USE_GH_CLI" = true ]; then
    read -p "Do you want to create environments using GitHub CLI? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        gh api repos/:owner/:repo/environments/development --method PUT || echo "Development environment created/updated"
        gh api repos/:owner/:repo/environments/production --method PUT || echo "Production environment created/updated"
        echo -e "${GREEN}✅ Environments created${NC}"
    fi
fi

echo ""
echo "=========================================="
echo "Step 4: Verify Terraform State Backend"
echo "=========================================="
echo ""

read -p "Do you want to set up Terraform state backend? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    cd infrastructure
    if [ -f setup-state-bucket.sh ]; then
        chmod +x setup-state-bucket.sh
        ./setup-state-bucket.sh "$AWS_REGION"
        echo -e "${GREEN}✅ Terraform state backend configured${NC}"
    else
        echo -e "${YELLOW}⚠️  setup-state-bucket.sh not found${NC}"
    fi
    cd ..
fi

echo ""
echo "=========================================="
echo "Step 5: Test CI/CD Pipeline"
echo "=========================================="
echo ""

echo "To test the pipeline:"
echo "1. Create a test branch:"
echo "   git checkout -b test-ci-cd"
echo ""
echo "2. Make a small change:"
echo "   echo '# Test CI/CD' >> README.md"
echo "   git add README.md"
echo "   git commit -m 'Test CI/CD pipeline'"
echo "   git push origin test-ci-cd"
echo ""
echo "3. Create a PR to 'develop' branch"
echo "4. Check the Actions tab to see workflow run"
echo ""

echo -e "${GREEN}✅ CI/CD Setup Complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Add GitHub Secrets (see instructions above)"
echo "2. Create GitHub Environments"
echo "3. Test the pipeline with a test branch"
echo "4. Review DEPLOYMENT_ROADMAP.md for full deployment guide"
echo ""

