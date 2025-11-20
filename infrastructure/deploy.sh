#!/bin/bash
# Deployment script for LLM Duel Arena

set -e

ENVIRONMENT=${1:-dev}
REGION=${2:-us-east-1}

echo "🚀 Deploying LLM Duel Arena to $ENVIRONMENT in $REGION"

# Step 1: Build Lambda deployment packages
echo "📦 Building Lambda packages..."
mkdir -p deployments

# Game service
cd ../app
zip -r ../infrastructure/deployments/game.zip \
    services/game_manager.py \
    services/base_game.py \
    services/chess_engine.py \
    services/tic_tac_toe_engine.py \
    services/rps_engine.py \
    services/racing_engine.py \
    services/word_association_engine.py \
    lambda_handlers/game_handler.py \
    -x "*.pyc" "__pycache__/*" "*.db"

# Auth service
zip -r ../infrastructure/deployments/auth.zip \
    routers/auth.py \
    lambda_handlers/auth_handler.py \
    -x "*.pyc" "__pycache__/*"

# LLM service
zip -r ../infrastructure/deployments/llm.zip \
    models/base.py \
    models/ollama_adapter.py \
    models/openai_adapter.py \
    models/anthropic_adapter.py \
    lambda_handlers/llm_handler.py \
    -x "*.pyc" "__pycache__/*"

cd ../infrastructure

# Step 2: Initialize Terraform (if needed)
if [ ! -d ".terraform" ]; then
    echo "🔧 Initializing Terraform..."
    terraform init
fi

# Step 3: Plan
echo "📋 Planning deployment..."
terraform plan -var="environment=$ENVIRONMENT" -var="aws_region=$REGION"

# Step 4: Apply
read -p "Continue with deployment? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 Applying Terraform..."
    terraform apply -var="environment=$ENVIRONMENT" -var="aws_region=$REGION" -auto-approve
    
    echo "✅ Deployment complete!"
    echo ""
    echo "📊 Outputs:"
    terraform output
else
    echo "❌ Deployment cancelled"
fi

