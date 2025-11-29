#!/bin/bash
# Deploy static assets to S3 and invalidate CloudFront cache

set -e

ENVIRONMENT=${1:-dev}
REGION=${2:-us-east-1}

if [ ! -d "../infrastructure/environments/${ENVIRONMENT}" ]; then
  echo "❌ Environment directory 'environments/${ENVIRONMENT}' not found."
  exit 1
fi

echo "📦 Deploying static assets for ${ENVIRONMENT}..."

cd "../infrastructure/environments/${ENVIRONMENT}"

# Get S3 bucket name from Terraform output
BUCKET_NAME=$(terraform output -raw s3_bucket_name 2>/dev/null || echo "")
CLOUDFRONT_ID=$(terraform output -raw cloudfront_distribution_id 2>/dev/null || echo "")

if [ -z "$BUCKET_NAME" ]; then
  echo "❌ Could not get S3 bucket name from Terraform. Make sure infrastructure is deployed."
  exit 1
fi

echo "📤 Uploading to S3 bucket: ${BUCKET_NAME}"

# Upload static files
cd ../../..
aws s3 sync app/static/ s3://${BUCKET_NAME}/static/ \
  --region ${REGION} \
  --delete \
  --exclude "*.pyc" \
  --exclude "__pycache__/*"

# Upload templates
aws s3 sync app/templates/ s3://${BUCKET_NAME}/ \
  --region ${REGION} \
  --delete \
  --exclude "*.pyc" \
  --exclude "__pycache__/*"

echo "✅ Static assets uploaded!"

# Invalidate CloudFront cache if distribution exists
if [ -n "$CLOUDFRONT_ID" ]; then
  echo "🔄 Invalidating CloudFront cache..."
  INVALIDATION_ID=$(aws cloudfront create-invalidation \
    --distribution-id ${CLOUDFRONT_ID} \
    --paths "/*" \
    --region ${REGION} \
    --query 'Invalidation.Id' \
    --output text)
  
  echo "✅ CloudFront invalidation created: ${INVALIDATION_ID}"
  echo "⏳ Cache invalidation may take 5-15 minutes to complete."
else
  echo "⚠️  CloudFront distribution ID not found. Skipping cache invalidation."
fi

echo "✅ Static assets deployment complete!"








