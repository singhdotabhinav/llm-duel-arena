# Quick Start - Local Testing

## Prerequisites Check

Before starting, make sure you have:

1. ✅ **Cognito configured** (you have `COGNITO_DOMAIN` set)
2. ⚠️ **Python 3.12+** (you have 3.9.6 - may need to upgrade)
3. ⚠️ **Ollama running** (for local LLM models)

## Step 1: Start Ollama (Required for LLM Models)

Open a **new terminal** and run:

```bash
ollama serve
```

Keep this terminal open. In another terminal, pull the models:

```bash
ollama pull llama3.1
ollama pull mistral-nemo
```

## Step 2: Activate Virtual Environment

```bash
cd /Users/abhinav/projects/llm-duel-arena
source venv/bin/activate
```

## Step 3: Install/Update Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## Step 4: Verify Environment Variables

Make sure your `.env` file has:

```bash
USE_COGNITO=true
COGNITO_USER_POOL_ID=us-east-1_7fscSPSUe
COGNITO_CLIENT_ID=2v96lg57eesiuln067hh5mgol9
COGNITO_DOMAIN=us-east-17fscspsue.auth.us-east-1.amazoncognito.com
COGNITO_REGION=us-east-1
COGNITO_CALLBACK_URL=http://localhost:8000/auth/callback
COGNITO_LOGOUT_URL=http://localhost:8000/
APP_SECRET_KEY=your-secret-key-here
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1
DYNAMODB_TABLE_NAME=llm-duel-arena-games-int
```

## Step 5: Run the Application

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Step 6: Access the Application

Open your browser:
- **http://localhost:8000**

## Step 7: Test Authentication

1. Click "Sign Up" or "Login"
2. You'll be redirected to Cognito Hosted UI
3. Create an account or login
4. You'll be redirected back to `http://localhost:8000/auth/callback`

## Troubleshooting

### Python Version Issue

If you get Python version errors, you may need Python 3.12+. Options:

1. **Install Python 3.12+**:
   ```bash
   # macOS with Homebrew
   brew install python@3.12
   
   # Then create new venv
   python3.12 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Or try with Python 3.9** (may work for basic testing):
   ```bash
   # Some features might not work, but basic app should run
   ```

### Ollama Not Running

Make sure Ollama is running:
```bash
# Check if running
curl http://localhost:11434/api/tags

# Start if not running
ollama serve
```

### Cognito Errors

- Make sure `http://localhost:8000/auth/callback` is in Cognito App Client allowed callback URLs
- Verify all Cognito environment variables are correct
- Check that `USE_COGNITO=true`

### DynamoDB Errors

- Make sure AWS credentials are correct
- Verify DynamoDB table exists: `llm-duel-arena-games-int`
- Check AWS region matches your table region

## Quick Commands Reference

```bash
# Start Ollama (in separate terminal)
ollama serve

# Activate venv
source venv/bin/activate

# Run app
uvicorn app.main:app --reload

# Check Ollama models
ollama list

# Pull models if needed
ollama pull llama3.1
ollama pull mistral-nemo
```

