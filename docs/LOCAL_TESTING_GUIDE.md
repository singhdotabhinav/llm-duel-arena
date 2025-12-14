# Local Testing Guide

This guide will help you test the LLM Duel Arena application locally without needing a domain.

## Prerequisites

1. **Python 3.13+** (or 3.12+)
2. **AWS Account** (for Cognito and DynamoDB)
3. **Ollama** (for local LLM models) - Optional but recommended
4. **AWS CLI** configured (optional, for easier setup)

## Step 1: Set Up AWS Cognito User Pool

Since the app requires Cognito authentication, you'll need to create a Cognito User Pool in AWS.

### 📖 Detailed Setup Guide

**👉 See [COGNITO_SETUP_GUIDE.md](COGNITO_SETUP_GUIDE.md) for complete step-by-step instructions with screenshots guidance.**

### Quick Summary

1. Go to AWS Console → Cognito → Create user pool
2. Configure sign-in with Email
3. Create app client **without secret** (public client)
4. Set callback URL: `http://localhost:8000/auth/callback`
5. Create Cognito domain
6. Copy User Pool ID, Client ID, and Domain to your `.env` file

### Option A: Use Existing Cognito Pool (If Already Deployed)

If you've already deployed the infrastructure via Terraform, you can use the existing Cognito User Pool:

1. Go to AWS Console → Cognito → User Pools
2. Find your user pool (likely named `llm-duel-arena-*`)
3. Note down:
   - **User Pool ID** (e.g., `us-east-1_XXXXXXXXX`)
   - **App Client ID** (from App integration → App clients)
   - **Region** (e.g., `us-east-1`)
4. Make sure the app client has `http://localhost:8000/auth/callback` in allowed callback URLs

## Step 2: Set Up DynamoDB Tables

You need DynamoDB tables for storing games and users. You can use AWS DynamoDB or local DynamoDB.

### Option A: Use AWS DynamoDB (Recommended)

1. Go to AWS Console → DynamoDB → Tables
2. Create tables if they don't exist:
   - **Games table**: `llm-duel-arena-games-int` (or `-prod`)
   - **Users table**: `llm-duel-arena-users-int` (or `-prod`)
3. Or use Terraform outputs from your deployment:
   ```bash
   cd infrastructure/environments/int
   terraform output dynamodb_table_name
   terraform output users_table_name
   ```

### Option B: Use Local DynamoDB (Advanced)

For completely local testing without AWS:

1. Install DynamoDB Local:
   ```bash
   docker run -p 8000:8000 amazon/dynamodb-local
   ```
2. Update `.env`:
   ```bash
   AWS_ENDPOINT_URL=http://localhost:8000
   ```

## Step 3: Install Ollama (For Local LLM Models)

1. **Install Ollama**: https://ollama.ai/download
2. **Start Ollama**:
   ```bash
   ollama serve
   ```
3. **Pull models**:
   ```bash
   ollama pull llama3.1
   ollama pull mistral-nemo
   ```

## Step 4: Configure Environment Variables

1. **Copy example env file**:
   ```bash
   cp env.example .env
   ```

2. **Update `.env` with your settings**:

```bash
# Server
APP_NAME=LLM Duel Arena
APP_DEBUG=true
APP_SECRET_KEY=your-random-secret-key-minimum-32-characters-long

# AWS Cognito (REQUIRED)
USE_COGNITO=true
COGNITO_USER_POOL_ID=us-east-1_XXXXXXXXX  # From Step 1
COGNITO_CLIENT_ID=your-app-client-id      # From Step 1
COGNITO_REGION=us-east-1                  # Your Cognito region
COGNITO_DOMAIN=llm-duel-arena-local.auth.us-east-1.amazoncognito.com  # From Step 1
COGNITO_CALLBACK_URL=http://localhost:8000/auth/callback
COGNITO_LOGOUT_URL=http://localhost:8000/

# AWS Credentials (for DynamoDB access)
AWS_ACCESS_KEY_ID=your-access-key-id
AWS_SECRET_ACCESS_KEY=your-secret-access-key
AWS_REGION=us-east-1

# DynamoDB Tables
DYNAMODB_TABLE_NAME=llm-duel-arena-games-int  # Your games table name
SESSION_TABLE_NAME=LLM-Duel-Sessions          # Optional, for session storage

# Models (using Ollama locally)
DEFAULT_WHITE_MODEL=ollama:llama3.1:latest
DEFAULT_BLACK_MODEL=ollama:mistral-nemo:latest

# CORS (for local development)
CORS_ORIGINS=http://localhost:8000,http://127.0.0.1:8000

# Deployment mode
DEPLOYMENT_MODE=local
```

### Generate Secret Key

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Step 5: Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Step 6: Run the Application

```bash
# Make sure Ollama is running
ollama serve

# In another terminal, run the app
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Step 7: Access the Application

Open your browser and navigate to:
- **http://localhost:8000** (recommended for Cognito callbacks)
- **http://127.0.0.1:8000** (also works)

## Step 8: Test Authentication

1. Click "Sign Up" or "Login"
2. You'll be redirected to Cognito hosted UI
3. Create a test user or login
4. You'll be redirected back to `http://localhost:8000/auth/callback`
5. You should be logged in and can start playing games!

## Troubleshooting

### Issue: "Cognito authentication is required"

**Solution**: Make sure `USE_COGNITO=true` in your `.env` file.

### Issue: "Invalid redirect URI"

**Solution**: 
1. Check that your Cognito App Client has `http://localhost:8000/auth/callback` in allowed callback URLs
2. Make sure you're using `localhost` (not `127.0.0.1`) in the callback URL

### Issue: "DynamoDB table not found"

**Solution**:
1. Verify the table name in `.env` matches your DynamoDB table
2. Check AWS credentials are correct
3. Verify AWS region matches your table region

### Issue: "Ollama connection failed"

**Solution**:
1. Make sure Ollama is running: `ollama serve`
2. Test Ollama: `ollama list`
3. Pull models: `ollama pull llama3.1`

### Issue: CORS errors

**Solution**: Make sure `CORS_ORIGINS` includes `http://localhost:8000` in your `.env`

## Testing Without Cognito (Not Recommended)

If you want to test without Cognito (for development only), you would need to modify the code to bypass authentication. However, this is **not recommended** as it breaks the production flow.

## Next Steps

Once local testing works:
1. Test game creation and gameplay
2. Test user authentication flow
3. Test game history and user dashboard
4. Verify DynamoDB is storing data correctly

## Quick Test Checklist

- [ ] Cognito User Pool created
- [ ] Cognito App Client configured with localhost callback
- [ ] DynamoDB tables exist
- [ ] `.env` file configured correctly
- [ ] Ollama running and models pulled
- [ ] Dependencies installed
- [ ] Application starts without errors
- [ ] Can access http://localhost:8000
- [ ] Can sign up/login via Cognito
- [ ] Can create and play games

## Cost Considerations

For local testing with AWS services:
- **Cognito**: Free tier includes 50,000 MAU (Monthly Active Users)
- **DynamoDB**: Free tier includes 25 GB storage and 25 read/write capacity units
- **Data Transfer**: Minimal for local testing

You should stay well within free tier limits for local development.

