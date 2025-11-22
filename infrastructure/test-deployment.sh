#!/bin/bash
# Test deployment script - validates configuration before deploying

set -e

ENVIRONMENT=${1:-dev}
REGION=${2:-us-east-1}

echo "🧪 Testing deployment configuration for ${ENVIRONMENT}..."
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check functions
check_command() {
    if command -v $1 &> /dev/null; then
        echo -e "${GREEN}✅${NC} $1 is installed"
        return 0
    else
        echo -e "${RED}❌${NC} $1 is not installed"
        return 1
    fi
}

check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✅${NC} $1 exists"
        return 0
    else
        echo -e "${RED}❌${NC} $1 is missing"
        return 1
    fi
}

# Test results
TESTS_PASSED=0
TESTS_FAILED=0

# 1. Check prerequisites
echo "📋 Checking prerequisites..."
echo ""

check_command "terraform" && TESTS_PASSED=$((TESTS_PASSED+1)) || TESTS_FAILED=$((TESTS_FAILED+1))
check_command "aws" && TESTS_PASSED=$((TESTS_PASSED+1)) || TESTS_FAILED=$((TESTS_FAILED+1))
check_command "python3" && TESTS_PASSED=$((TESTS_PASSED+1)) || TESTS_FAILED=$((TESTS_FAILED+1))
check_command "zip" && TESTS_PASSED=$((TESTS_PASSED+1)) || TESTS_FAILED=$((TESTS_FAILED+1))

echo ""

# 2. Check AWS credentials
echo "🔐 Checking AWS credentials..."
if aws sts get-caller-identity &> /dev/null; then
    echo -e "${GREEN}✅${NC} AWS credentials configured"
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    echo "   Account ID: ${ACCOUNT_ID}"
    TESTS_PASSED=$((TESTS_PASSED+1))
else
    echo -e "${RED}❌${NC} AWS credentials not configured"
    echo "   Run: aws configure"
    TESTS_FAILED=$((TESTS_FAILED+1))
fi
echo ""

# 3. Check environment directory
echo "📁 Checking environment structure..."
ENV_DIR="environments/${ENVIRONMENT}"
if [ -d "$ENV_DIR" ]; then
    echo -e "${GREEN}✅${NC} Environment directory exists: ${ENV_DIR}"
    TESTS_PASSED=$((TESTS_PASSED+1))
    
    check_file "${ENV_DIR}/main.tf" && TESTS_PASSED=$((TESTS_PASSED+1)) || TESTS_FAILED=$((TESTS_FAILED+1))
    check_file "${ENV_DIR}/backend.tf" && TESTS_PASSED=$((TESTS_PASSED+1)) || TESTS_FAILED=$((TESTS_FAILED+1))
    check_file "${ENV_DIR}/variables.tf" && TESTS_PASSED=$((TESTS_PASSED+1)) || TESTS_FAILED=$((TESTS_FAILED+1))
    
    if [ -f "${ENV_DIR}/terraform.tfvars" ]; then
        echo -e "${GREEN}✅${NC} terraform.tfvars exists"
        TESTS_PASSED=$((TESTS_PASSED+1))
    else
        echo -e "${YELLOW}⚠️${NC}  terraform.tfvars not found (using terraform.tfvars.example)"
        if [ -f "${ENV_DIR}/terraform.tfvars.example" ]; then
            echo -e "${GREEN}✅${NC} terraform.tfvars.example exists"
            TESTS_PASSED=$((TESTS_PASSED+1))
        else
            echo -e "${RED}❌${NC} terraform.tfvars.example not found"
            TESTS_FAILED=$((TESTS_FAILED+1))
        fi
    fi
else
    echo -e "${RED}❌${NC} Environment directory not found: ${ENV_DIR}"
    TESTS_FAILED=$((TESTS_FAILED+1))
fi
echo ""

# 4. Check Terraform modules
echo "🔧 Checking Terraform modules..."
MODULE_DIR="modules/core"
if [ -d "$MODULE_DIR" ]; then
    echo -e "${GREEN}✅${NC} Core module exists"
    TESTS_PASSED=$((TESTS_PASSED+1))
    
    REQUIRED_FILES=("data.tf" "variables.tf" "outputs.tf" "lambda.tf" "api_gateway.tf" "dynamodb.tf" "iam.tf" "s3.tf" "cloudfront.tf" "secrets.tf")
    for file in "${REQUIRED_FILES[@]}"; do
        if [ -f "${MODULE_DIR}/${file}" ]; then
            echo -e "  ${GREEN}✅${NC} ${file}"
            TESTS_PASSED=$((TESTS_PASSED+1))
        else
            echo -e "  ${RED}❌${NC} ${file} missing"
            TESTS_FAILED=$((TESTS_FAILED+1))
        fi
    done
else
    echo -e "${RED}❌${NC} Core module not found: ${MODULE_DIR}"
    TESTS_FAILED=$((TESTS_FAILED+1))
fi
echo ""

# 5. Check application code
echo "💻 Checking application code..."
check_file "../app/lambda_handlers/game_handler.py" && TESTS_PASSED=$((TESTS_PASSED+1)) || TESTS_FAILED=$((TESTS_FAILED+1))
check_file "../app/lambda_handlers/auth_handler.py" && TESTS_PASSED=$((TESTS_PASSED+1)) || TESTS_FAILED=$((TESTS_FAILED+1))
check_file "../app/lambda_handlers/llm_handler.py" && TESTS_PASSED=$((TESTS_PASSED+1)) || TESTS_FAILED=$((TESTS_FAILED+1))
check_file "../app/services/dynamodb_service.py" && TESTS_PASSED=$((TESTS_PASSED+1)) || TESTS_FAILED=$((TESTS_FAILED+1))
check_file "../requirements-lambda.txt" && TESTS_PASSED=$((TESTS_PASSED+1)) || TESTS_FAILED=$((TESTS_FAILED+1))
echo ""

# 6. Check deployment scripts
echo "📜 Checking deployment scripts..."
check_file "deploy.sh" && TESTS_PASSED=$((TESTS_PASSED+1)) || TESTS_FAILED=$((TESTS_FAILED+1))
check_file "build-lambda.sh" && TESTS_PASSED=$((TESTS_PASSED+1)) || TESTS_FAILED=$((TESTS_FAILED+1))
check_file "deploy-static.sh" && TESTS_PASSED=$((TESTS_PASSED+1)) || TESTS_FAILED=$((TESTS_FAILED+1))
check_file "setup-state-bucket.sh" && TESTS_PASSED=$((TESTS_PASSED+1)) || TESTS_FAILED=$((TESTS_FAILED+1))

# Check if scripts are executable
if [ -x "deploy.sh" ]; then
    echo -e "  ${GREEN}✅${NC} deploy.sh is executable"
    TESTS_PASSED=$((TESTS_PASSED+1))
else
    echo -e "  ${YELLOW}⚠️${NC}  deploy.sh is not executable (run: chmod +x deploy.sh)"
fi
echo ""

# 7. Validate Terraform configuration
echo "🔍 Validating Terraform configuration..."
if command -v terraform &> /dev/null; then
    cd "${ENV_DIR}"
    if terraform init -backend=false &> /dev/null; then
        echo -e "${GREEN}✅${NC} Terraform can initialize"
        TESTS_PASSED=$((TESTS_PASSED+1))
        
        if terraform validate &> /dev/null; then
            echo -e "${GREEN}✅${NC} Terraform configuration is valid"
            TESTS_PASSED=$((TESTS_PASSED+1))
        else
            echo -e "${RED}❌${NC} Terraform configuration has errors"
            terraform validate
            TESTS_FAILED=$((TESTS_FAILED+1))
        fi
    else
        echo -e "${RED}❌${NC} Terraform initialization failed"
        TESTS_FAILED=$((TESTS_FAILED+1))
    fi
    cd ../..
else
    echo -e "${YELLOW}⚠️${NC}  Terraform not installed - skipping validation"
    echo "   Install Terraform to validate configuration"
fi
echo ""

# 8. Check S3 state bucket (optional)
echo "🪣 Checking Terraform state bucket..."
BUCKET_NAME="llm-duel-arena-terraform-state"
if aws s3 ls "s3://${BUCKET_NAME}" &> /dev/null; then
    echo -e "${GREEN}✅${NC} State bucket exists: ${BUCKET_NAME}"
    TESTS_PASSED=$((TESTS_PASSED+1))
else
    echo -e "${YELLOW}⚠️${NC}  State bucket not found (will be created by setup-state-bucket.sh)"
    echo "   Run: ./setup-state-bucket.sh ${REGION}"
fi
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Test Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✅ Passed: ${TESTS_PASSED}${NC}"
if [ $TESTS_FAILED -gt 0 ]; then
    echo -e "${RED}❌ Failed: ${TESTS_FAILED}${NC}"
    echo ""
    echo "Fix the errors above before deploying."
    exit 1
else
    echo -e "${GREEN}❌ Failed: ${TESTS_FAILED}${NC}"
    echo ""
    echo -e "${GREEN}✅ All tests passed! Ready to deploy.${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. cd environments/${ENVIRONMENT}"
    echo "  2. terraform init"
    echo "  3. terraform plan -var-file=terraform.tfvars"
    echo "  4. terraform apply -var-file=terraform.tfvars"
    exit 0
fi

