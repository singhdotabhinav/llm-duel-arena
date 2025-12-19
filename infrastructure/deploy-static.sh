#!/bin/bash
# Deploy static assets to S3 and invalidate CloudFront cache

set -e
set +H  # Disable history expansion to avoid issues with ! in paths

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
  echo "   Distribution ID: ${CLOUDFRONT_ID}"
  # Temporarily disable exit on error for CloudFront invalidation
  set +e
  INVALIDATION_OUTPUT=$(aws cloudfront create-invalidation \
    --distribution-id "${CLOUDFRONT_ID}" \
    --paths "/*" \
    --query 'Invalidation.Id' \
    --output text 2>&1)
  INVALIDATION_EXIT_CODE=$?
  set -e
  
  if [ $INVALIDATION_EXIT_CODE -eq 0 ] && [ -n "$INVALIDATION_OUTPUT" ] && [[ ! "$INVALIDATION_OUTPUT" =~ [Ee]rror ]]; then
    echo "✅ CloudFront invalidation created: ${INVALIDATION_OUTPUT}"
    echo "⏳ Cache invalidation may take 5-15 minutes to complete."
  else
    echo "⚠️  CloudFront invalidation failed or skipped"
    echo "   Output: ${INVALIDATION_OUTPUT}"
    echo "   This is non-critical - static assets are already deployed."
  fi
else
  echo "⚠️  CloudFront distribution ID not found. Skipping cache invalidation."
fi

echo "✅ Static assets deployment complete!"











