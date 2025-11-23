#!/bin/bash
# Create S3 bucket and DynamoDB table for Terraform remote state
# Run this once before first Terraform deployment

set -e

REGION=${1:-us-east-1}
BUCKET_NAME="llm-duel-arena-terraform-state"
TABLE_NAME="llm-duel-arena-terraform-locks"

echo "🔧 Setting up Terraform state backend..."

# Check if bucket exists
if aws s3 ls "s3://${BUCKET_NAME}" 2>&1 | grep -q 'NoSuchBucket'; then
  echo "📦 Creating S3 bucket: ${BUCKET_NAME}"
  
  # Create bucket
  if [ "$REGION" == "us-east-1" ]; then
    aws s3api create-bucket \
      --bucket ${BUCKET_NAME} \
      --region ${REGION}
  else
    aws s3api create-bucket \
      --bucket ${BUCKET_NAME} \
      --region ${REGION} \
      --create-bucket-configuration LocationConstraint=${REGION}
  fi
  
  # Enable versioning
  aws s3api put-bucket-versioning \
    --bucket ${BUCKET_NAME} \
    --versioning-configuration Status=Enabled
  
  # Enable encryption
  aws s3api put-bucket-encryption \
    --bucket ${BUCKET_NAME} \
    --server-side-encryption-configuration '{
      "Rules": [{
        "ApplyServerSideEncryptionByDefault": {
          "SSEAlgorithm": "AES256"
        }
      }]
    }'
  
  # Block public access
  aws s3api put-public-access-block \
    --bucket ${BUCKET_NAME} \
    --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
  
  echo "✅ S3 bucket created and configured"
else
  echo "✅ S3 bucket already exists"
fi

# Check if DynamoDB table exists
if aws dynamodb describe-table --table-name ${TABLE_NAME} --region ${REGION} 2>&1 | grep -q 'ResourceNotFoundException'; then
  echo "📊 Creating DynamoDB table: ${TABLE_NAME}"
  
  aws dynamodb create-table \
    --table-name ${TABLE_NAME} \
    --attribute-definitions AttributeName=LockID,AttributeType=S \
    --key-schema AttributeName=LockID,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region ${REGION} \
    --tags Key=Name,Value=TerraformStateLocks Key=Project,Value=llm-duel-arena
  
  echo "⏳ Waiting for table to be active..."
  aws dynamodb wait table-exists --table-name ${TABLE_NAME} --region ${REGION}
  
  echo "✅ DynamoDB table created"
else
  echo "✅ DynamoDB table already exists"
fi

echo ""
echo "✅ Terraform state backend setup complete!"
echo ""
echo "You can now run:"
echo "  cd infrastructure/environments/dev"
echo "  terraform init"
echo "  terraform plan -var-file=terraform.tfvars"





