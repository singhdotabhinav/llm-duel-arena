# How to Run Tests

## Quick Start

### Run Local Application Test

```bash
cd /Users/abhinav/projects/llm-duel-arena
./test-local-app.sh
```

That's it! The script will:
1. Start the FastAPI server automatically (if not running)
2. Test all endpoints
3. Stop the server when done

## Detailed Instructions

### Option 1: Run with Existing Server

If you already have the server running on port 8000:

```bash
cd /Users/abhinav/projects/llm-duel-arena
./test-local-app.sh
```

The script will detect the running server and use it for tests.

### Option 2: Let Script Start Server

If no server is running, the script will:
1. Start the server automatically
2. Wait for it to be ready
3. Run all tests
4. Stop the server when done

```bash
cd /Users/abhinav/projects/llm-duel-arena
./test-local-app.sh
```

### Option 3: Manual Server + Test

1. **Start server manually** (in one terminal):
   ```bash
   cd /Users/abhinav/projects/llm-duel-arena
   source venv/bin/activate
   uvicorn app.main:app --reload
   ```

2. **Run tests** (in another terminal):
   ```bash
   cd /Users/abhinav/projects/llm-duel-arena
   ./test-local-app.sh
   ```

## What the Test Does

The script tests:

✅ **Frontend Pages:**
- Landing page (`/`)
- Game page (`/game`)
- Games list (`/games`)
- My games (`/my-games`)
- Static files (`/static/css/styles.css`)

✅ **API Endpoints:**
- Game creation (`POST /api/games/`)
- Get game state (`GET /api/games/{game_id}`)
- List games (`GET /api/games/list`)
- Health check (`GET /api/games/health`)
- Auth login (`GET /auth/login`)

## Troubleshooting

### Permission Denied

If you get "Permission denied", make the script executable:

```bash
chmod +x test-local-app.sh
```

### Port Already in Use

If port 8000 is already in use by another application:

1. Stop the other application, OR
2. The script will use the existing server on port 8000

### Server Won't Start

Check if dependencies are installed:

```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Tests Fail

Check the server logs:

```bash
tail -f /tmp/llm-duel-arena-test.log
```

## Other Test Scripts

### Test Local Setup

```bash
cd infrastructure
./test-local.sh
```

This validates:
- Python dependencies
- Imports
- Configuration
- Ollama connection

### Test Deployment Configuration

```bash
cd infrastructure
./test-deployment.sh dev
```

This validates:
- Terraform installation
- AWS CLI setup
- Configuration files
- Environment structure

## Expected Output

When tests pass, you'll see:

```
🧪 Testing Local LLM Duel Arena Application
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Landing page (HTTP 200)
✅ Game page (no game_id) (HTTP 200)
✅ Games list page (HTTP 200)
✅ My games page (HTTP 200)
✅ Static CSS file (HTTP 200)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔌 Testing API Endpoints
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Game created successfully (ID: ...)
✅ Get game state (HTTP 200)
✅ List all games (HTTP 200)
✅ Health check (HTTP 200)
✅ Auth login endpoint (HTTP 302 - redirect)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Test Summary
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Passed: 10
❌ Failed: 0

✅ All tests passed!
```

## Next Steps

After tests pass:
1. ✅ Local application is working
2. ⏳ Test manually in browser at http://localhost:8000
3. ⏳ Ready for AWS deployment testing

---

**Quick Command:**
```bash
cd /Users/abhinav/projects/llm-duel-arena && ./test-local-app.sh
```




