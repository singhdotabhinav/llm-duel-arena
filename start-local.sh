#!/bin/bash
# Quick start script for local testing

set -e

echo "🚀 Starting LLM Duel Arena Locally"
echo "=================================="
echo ""

# Activate virtual environment
if [ -d "venv" ]; then
    echo "🔌 Activating virtual environment..."
    source venv/bin/activate
else
    echo "❌ Virtual environment not found. Run: python3 -m venv venv"
    exit 1
fi

# Check Ollama
echo "🤖 Checking Ollama..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✅ Ollama is running"
else
    echo "⚠️  Ollama is not running"
    echo "   Please start Ollama in another terminal: ollama serve"
    echo "   Then pull models: ollama pull llama3.1 && ollama pull mistral-nemo"
    echo ""
    read -p "Press Enter to continue anyway, or Ctrl+C to start Ollama first..."
fi

# Check environment variables
echo ""
echo "🔍 Checking environment..."
if [ -f ".env" ]; then
    source .env 2>/dev/null || true
    if [ "$USE_COGNITO" != "true" ]; then
        echo "⚠️  USE_COGNITO is not set to 'true'"
    fi
    if [ -z "$COGNITO_DOMAIN" ]; then
        echo "⚠️  COGNITO_DOMAIN is not set"
    else
        echo "✅ COGNITO_DOMAIN: $COGNITO_DOMAIN"
    fi
else
    echo "⚠️  .env file not found"
fi

echo ""
echo "🌐 Starting application..."
echo "   Access at: http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Start the application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000





