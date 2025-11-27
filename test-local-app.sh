#!/bin/bash
# Comprehensive local application test

set -e

echo "🧪 Testing Local LLM Duel Arena Application"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check if server is already running
if curl -s http://localhost:8000 &> /dev/null; then
    echo -e "${YELLOW}⚠️${NC}  Server appears to be running on port 8000"
    echo "   Using existing server for tests"
    SERVER_RUNNING=true
else
    echo -e "${BLUE}ℹ️${NC}  Starting test server..."
    SERVER_RUNNING=false
    
    # Activate venv and start server in background
    source venv/bin/activate
    uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/llm-duel-arena-test.log 2>&1 &
    SERVER_PID=$!
    
    echo "   Server starting (PID: $SERVER_PID)..."
    sleep 3
    
    # Wait for server to be ready
    for i in {1..10}; do
        if curl -s http://localhost:8000 &> /dev/null; then
            echo -e "${GREEN}✅${NC} Server is ready"
            break
        fi
        if [ $i -eq 10 ]; then
            echo -e "${RED}❌${NC} Server failed to start"
            cat /tmp/llm-duel-arena-test.log
            kill $SERVER_PID 2>/dev/null || true
            exit 1
        fi
        sleep 1
    done
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 Testing Endpoints"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

BASE_URL="http://localhost:8000"
TESTS_PASSED=0
TESTS_FAILED=0

# Test function
test_endpoint() {
    local method=$1
    local endpoint=$2
    local expected_status=$3
    local description=$4
    local data=$5
    
    if [ -z "$description" ]; then
        description="$method $endpoint"
    fi
    
    if [ "$method" == "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "${BASE_URL}${endpoint}")
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" "${BASE_URL}${endpoint}" \
            -H "Content-Type: application/json" \
            -d "$data")
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" == "$expected_status" ]; then
        echo -e "${GREEN}✅${NC} $description (HTTP $http_code)"
        TESTS_PASSED=$((TESTS_PASSED+1))
        return 0
    else
        echo -e "${RED}❌${NC} $description (Expected $expected_status, got $http_code)"
        echo "   Response: ${body:0:100}..."
        TESTS_FAILED=$((TESTS_FAILED+1))
        return 1
    fi
}

# Test landing page
test_endpoint "GET" "/" "200" "Landing page"

# Test game page
test_endpoint "GET" "/game" "200" "Game page (no game_id)"

# Test games list page
test_endpoint "GET" "/games" "200" "Games list page"

# Test my-games page
test_endpoint "GET" "/my-games" "200" "My games page"

# Test static files
test_endpoint "GET" "/static/css/styles.css" "200" "Static CSS file"

# Test API endpoints
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔌 Testing API Endpoints"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Test create game endpoint
echo "Testing game creation..."
CREATE_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/games/" \
    -H "Content-Type: application/json" \
    -d '{
        "game_type": "chess",
        "white_model": "ollama:llama3.1:latest",
        "black_model": "ollama:mistral-nemo:latest"
    }')

if echo "$CREATE_RESPONSE" | grep -q "game_id"; then
    GAME_ID=$(echo "$CREATE_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['game_id'])" 2>/dev/null || echo "")
    if [ -n "$GAME_ID" ]; then
        echo -e "${GREEN}✅${NC} Game created successfully (ID: ${GAME_ID:0:8}...)"
        TESTS_PASSED=$((TESTS_PASSED+1))
        
        # Test get game state
        test_endpoint "GET" "/api/games/${GAME_ID}" "200" "Get game state"
        
        # Test list games
        test_endpoint "GET" "/api/games/list" "200" "List all games"
        
        # Test health endpoint
        test_endpoint "GET" "/api/games/health" "200" "Health check"
    else
        echo -e "${RED}❌${NC} Game created but couldn't extract game_id"
        TESTS_FAILED=$((TESTS_FAILED+1))
    fi
else
    echo -e "${RED}❌${NC} Game creation failed"
    echo "   Response: ${CREATE_RESPONSE:0:200}"
    TESTS_FAILED=$((TESTS_FAILED+1))
fi

# Test auth endpoints (should redirect or return appropriate response)
echo ""
# Accept both 302 and 307 as valid redirects
AUTH_RESPONSE=$(curl -s -w "\n%{http_code}" "${BASE_URL}/auth/login")
AUTH_CODE=$(echo "$AUTH_RESPONSE" | tail -n1)
if [ "$AUTH_CODE" == "302" ] || [ "$AUTH_CODE" == "307" ]; then
    echo -e "${GREEN}✅${NC} Auth login endpoint (HTTP $AUTH_CODE - redirect)"
    TESTS_PASSED=$((TESTS_PASSED+1))
else
    echo -e "${RED}❌${NC} Auth login endpoint (Expected 302/307, got $AUTH_CODE)"
    TESTS_FAILED=$((TESTS_FAILED+1))
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Test Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✅ Passed: ${TESTS_PASSED}${NC}"
if [ $TESTS_FAILED -gt 0 ]; then
    echo -e "${RED}❌ Failed: ${TESTS_FAILED}${NC}"
    echo ""
    echo "Check the server logs for details:"
    echo "  tail -f /tmp/llm-duel-arena-test.log"
    exit 1
else
    echo -e "${GREEN}❌ Failed: ${TESTS_FAILED}${NC}"
    echo ""
    echo -e "${GREEN}✅ All tests passed!${NC}"
fi

# Cleanup
if [ "$SERVER_RUNNING" == "false" ]; then
    echo ""
    echo "🛑 Stopping test server..."
    kill $SERVER_PID 2>/dev/null || true
    echo -e "${GREEN}✅${NC} Server stopped"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${BLUE}ℹ️${NC}  To start the server manually:"
echo "   cd $(pwd)"
echo "   source venv/bin/activate"
echo "   uvicorn app.main:app --reload"
echo ""
echo -e "${BLUE}ℹ️${NC}  Then visit: http://localhost:8000"
echo ""

