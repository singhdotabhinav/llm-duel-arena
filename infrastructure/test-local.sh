#!/bin/bash
# Test local FastAPI application (without AWS)

set -e

echo "🧪 Testing local FastAPI application..."
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

cd ..

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️${NC}  Virtual environment not found. Creating one..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install -q -r requirements.txt

# Check if database exists
if [ ! -f "llm_duel_arena.db" ]; then
    echo -e "${YELLOW}⚠️${NC}  Database not found. It will be created on first run."
fi

# Test imports
echo "🔍 Testing Python imports..."
python3 -c "
import sys
try:
    from app.main import app
    from app.core.config import settings
    from app.services.game_manager import GameManager
    print('✅ Core imports successful')
    
    # DynamoDB service is optional for local dev
    try:
        from app.services.dynamodb_service import DynamoDBService
        print('✅ DynamoDB service available (for AWS deployment)')
    except ImportError:
        print('⚠️  DynamoDB service not available (optional for local dev)')
except ImportError as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)
"

# Test configuration
echo "⚙️  Testing configuration..."
python3 -c "
from app.core.config import settings
assert settings.app_name, 'App name not set'
assert settings.secret_key != 'change_me', 'Secret key not changed!'
print('✅ Configuration valid')
print(f'   App name: {settings.app_name}')
print(f'   Deployment mode: {settings.deployment_mode}')
print(f'   Is local: {settings.is_local}')
"

# Check if Ollama is running (optional)
echo "🤖 Checking Ollama connection..."
if curl -s http://localhost:11434/api/tags &> /dev/null; then
    echo -e "${GREEN}✅${NC} Ollama is running"
    MODELS=$(curl -s http://localhost:11434/api/tags | python3 -c "import sys, json; data=json.load(sys.stdin); print(', '.join([m['name'] for m in data.get('models', [])]))" 2>/dev/null || echo "unknown")
    echo "   Available models: ${MODELS}"
else
    echo -e "${YELLOW}⚠️${NC}  Ollama is not running (optional for testing)"
    echo "   Start with: ollama serve"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✅ Local testing complete!${NC}"
echo ""
echo "To start the local server:"
echo "  uvicorn app.main:app --reload"
echo ""
echo "Then visit: http://localhost:8000"

