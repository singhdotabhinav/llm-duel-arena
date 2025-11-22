#!/bin/bash
# Deployment script for LLM Duel Arena

set -e

ENVIRONMENT=${1:-dev}
REGION=${2:-us-east-1}
ENV_DIR="environments/${ENVIRONMENT}"

if [ ! -d "$ENV_DIR" ]; then
  echo "❌ Environment directory '$ENV_DIR' not found."
  echo "Available environments:"
  ls environments
  exit 1
fi

echo "🚀 Deploying LLM Duel Arena to $ENVIRONMENT in $REGION"

echo "📦 Building Lambda packages..."
mkdir -p deployments

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

zip -r ../infrastructure/deployments/auth.zip \
    routers/auth.py \
    lambda_handlers/auth_handler.py \
    -x "*.pyc" "__pycache__/*"

zip -r ../infrastructure/deployments/llm.zip \
    models/base.py \
    models/ollama_adapter.py \
    models/openai_adapter.py \
    models/anthropic_adapter.py \
    lambda_handlers/llm_handler.py \
    -x "*.pyc" "__pycache__/*"

cd ../infrastructure

cd "$ENV_DIR"

TFVARS_FILE="terraform.tfvars"
VAR_FILE_ARG=""
if [ -f "$TFVARS_FILE" ]; then
  VAR_FILE_ARG="-var-file=$TFVARS_FILE"
else
  echo "⚠️  terraform.tfvars not found in $ENV_DIR (using defaults)"
fi

echo "🔧 Initializing Terraform..."
terraform init

echo "📋 Planning deployment..."
terraform plan $VAR_FILE_ARG

read -p "Continue with deployment? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
  echo "🚀 Applying Terraform..."
  terraform apply $VAR_FILE_ARG -auto-approve

  echo "✅ Deployment complete!"
  echo ""
  echo "📊 Outputs:"
  terraform output
else
  echo "❌ Deployment cancelled"
fi



