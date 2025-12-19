#!/bin/bash
# Quick local testing script for LLM Duel Arena

set -e

echo "🚀 LLM Duel Arena - Local Testing Setup"
echo "========================================"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "📋 Creating .env from env.example..."
    cp env.example .env
    echo "⚠️  Please update .env with your Cognito and AWS credentials"
    echo "   See docs/LOCAL_TESTING_GUIDE.md for details"
    echo ""
    read -p "Press Enter to continue after updating .env, or Ctrl+C to exit..."
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Check if Ollama is running
echo "🤖 Checking Ollama..."
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "⚠️  Ollama doesn't seem to be running"
    echo "   Please start Ollama: ollama serve"
    echo "   Then pull models: ollama pull llama3.1 && ollama pull mistral-nemo"
    echo ""
    read -p "Press Enter to continue anyway, or Ctrl+C to start Ollama first..."
else
    echo "✅ Ollama is running"
fi

# Check environment variables
echo "🔍 Checking environment variables..."
source .env 2>/dev/null || true

if [ -z "$COGNITO_USER_POOL_ID" ] || [ "$COGNITO_USER_POOL_ID" == "us-east-1_XXXXXXXXX" ]; then
    echo "⚠️  COGNITO_USER_POOL_ID not configured in .env"
fi

if [ -z "$COGNITO_CLIENT_ID" ] || [ "$COGNITO_CLIENT_ID" == "your-cognito-client-id" ]; then
    echo "⚠️  COGNITO_CLIENT_ID not configured in .env"
fi

if [ "$USE_COGNITO" != "true" ]; then
    echo "⚠️  USE_COGNITO is not set to 'true'"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "🌐 Starting application..."
echo "   Access at: http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Run the application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000





