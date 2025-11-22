#!/bin/bash
# Build Lambda deployment packages with dependencies

set -e

ENV=${1:-dev}
PACKAGE_DIR="lambda-packages"
DEPLOY_DIR="deployments"

echo "🔨 Building Lambda packages for $ENV..."

# Clean previous builds
rm -rf $PACKAGE_DIR $DEPLOY_DIR
mkdir -p $PACKAGE_DIR $DEPLOY_DIR

# Install dependencies to package directory
echo "📦 Installing dependencies..."
pip install -r ../requirements-lambda.txt -t $PACKAGE_DIR --upgrade

# Copy application code
echo "📋 Copying application code..."

# Game service
mkdir -p $PACKAGE_DIR/game
cp -r ../app/services $PACKAGE_DIR/game/
cp ../app/lambda_handlers/game_handler.py $PACKAGE_DIR/game/
cd $PACKAGE_DIR/game
zip -r ../../$DEPLOY_DIR/game.zip . -x "*.pyc" "__pycache__/*" "*.db" "*.log"
cd ../..

# Auth service
mkdir -p $PACKAGE_DIR/auth
cp -r ../app/routers $PACKAGE_DIR/auth/
cp -r ../app/services/dynamodb_service.py $PACKAGE_DIR/auth/services/
cp -r ../app/core $PACKAGE_DIR/auth/ 2>/dev/null || true
cp ../app/lambda_handlers/auth_handler.py $PACKAGE_DIR/auth/
cd $PACKAGE_DIR/auth
zip -r ../../$DEPLOY_DIR/auth.zip . -x "*.pyc" "__pycache__/*" "*.db" "*.log"
cd ../..

# LLM service
mkdir -p $PACKAGE_DIR/llm
cp -r ../app/models $PACKAGE_DIR/llm/
cp -r ../app/services/dynamodb_service.py $PACKAGE_DIR/llm/services/ 2>/dev/null || true
cp ../app/lambda_handlers/llm_handler.py $PACKAGE_DIR/llm/
cd $PACKAGE_DIR/llm
zip -r ../../$DEPLOY_DIR/llm.zip . -x "*.pyc" "__pycache__/*" "*.db" "*.log"
cd ../..

# Cleanup
rm -rf $PACKAGE_DIR

echo "✅ Lambda packages built successfully!"
echo "📦 Packages in: $DEPLOY_DIR/"
ls -lh $DEPLOY_DIR/




