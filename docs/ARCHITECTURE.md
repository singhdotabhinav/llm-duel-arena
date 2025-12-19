# LLM Duel Arena - Architecture Overview

## 🏗️ Current Architecture (AWS Deployment)

When you access your CloudFront URL (`https://d84l1y8p4kdic.cloudfront.net`), here's what happens:

### Request Flow

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │
       │ 1. Request HTML/CSS/JS
       ▼
┌─────────────────┐
│   CloudFront    │  ← CDN (Edge Locations)
│   Distribution  │
└──────┬──────────┘
       │
       │ 2. Serves static files from S3
       ▼
┌─────────────┐
│  S3 Bucket  │  ← Static Assets (HTML, CSS, JS, Images)
│  (Static)   │
└─────────────┘

┌─────────────┐
│   Browser   │
└──────┬──────┘
       │
       │ 3. JavaScript makes API calls
       │    (e.g., /api/games/create)
       ▼
┌──────────────────┐
│  API Gateway v2  │  ← HTTP API (REST Endpoint)
│  (HTTP API)      │
└──────┬───────────┘
       │
       │ 4. Routes to appropriate Lambda
       │    based on path (/api/games/* → game Lambda)
       ▼
┌─────────────────┐
│ Lambda Function │  ← Serverless Compute
│  (game/auth/llm)│
└──────┬──────────┘
       │
       │ 5. Lambda reads/writes data
       ▼
┌─────────────┐
│  DynamoDB   │  ← NoSQL Database (Games, Users)
└─────────────┘
```

## 📊 Detailed Component Breakdown

### 1. **CloudFront (CDN)**
- **Purpose**: Serves static files (HTML, CSS, JavaScript, images)
- **Origin**: S3 bucket (`llm-duel-arena-static-int-*`)
- **Caching**: Static assets cached at edge locations worldwide
- **URL**: `https://d84l1y8p4kdic.cloudfront.net`

**What runs here**: Nothing - just file serving

### 2. **S3 Bucket**
- **Purpose**: Stores static website files
- **Contents**: 
  - HTML templates (`index.html`, `landing.html`, etc.)
  - CSS files (`styles.css`, `racing.css`, etc.)
  - JavaScript files (`app.js`, `config.js`, etc.)
  - Images (`hero-image.jpg`, `favicon.svg`)

**What runs here**: Nothing - just storage

### 3. **API Gateway v2 (HTTP API)**
- **Purpose**: REST API endpoint that routes requests to Lambda functions
- **Routes**:
  - `/api/games/*` → `game` Lambda function
  - `/api/auth/*` → `auth` Lambda function  
  - `/api/llm/*` → `llm` Lambda function
- **URL**: `https://{api-id}.execute-api.us-east-1.amazonaws.com/int`

**What runs here**: Request routing only (no computation)

### 4. **Lambda Functions** (Serverless Compute)
- **Purpose**: Execute application logic
- **Functions**:
  - **`game` Lambda**: Handles game creation, moves, state management
  - **`auth` Lambda**: Handles authentication, user management
  - **`llm` Lambda**: Handles LLM API calls (Ollama, HuggingFace, etc.)
- **Runtime**: Python 3.12
- **Memory**: 256MB - 1024MB depending on function
- **Timeout**: 15-60 seconds

**What runs here**: ALL computation happens here!

### 5. **DynamoDB**
- **Purpose**: Stores game data and user information
- **Tables**:
  - `llm-duel-arena-games-int`: Game states, moves, results
  - `llm-duel-arena-users-int`: User accounts, profiles

**What runs here**: Database queries (no application logic)

### 6. **Cognito**
- **Purpose**: User authentication and authorization
- **Service**: Managed authentication service (not Lambda)

**What runs here**: Authentication logic (managed by AWS)

## 🔄 Complete Request Example

### Example: Creating a New Game

1. **User clicks "Start Game"** in browser
2. **JavaScript** (`app.js`) makes API call:
   ```javascript
   fetch('https://{api-gateway-url}/api/games/', {
     method: 'POST',
     body: JSON.stringify({game_type: 'chess'})
   })
   ```
3. **API Gateway** receives request at `/api/games/`
4. **API Gateway** routes to `game` Lambda function
5. **Lambda function** executes:
   - Validates request
   - Creates game state
   - Saves to DynamoDB
   - Returns game_id
6. **Response flows back**: Lambda → API Gateway → Browser
7. **JavaScript** receives response and updates UI

## 💻 Where Computation Happens

### ✅ **In the Cloud (AWS Lambda)**
- Game logic (chess moves, game state)
- LLM API calls (Ollama, HuggingFace)
- Authentication logic
- Data validation
- Business logic

### ❌ **NOT in Browser**
- No game computation in JavaScript
- JavaScript only handles:
  - UI rendering
  - User interactions
  - API calls (fetch requests)
  - Display updates

### ❌ **NOT in CloudFront/S3**
- Just static file serving
- No server-side processing

## 🌐 Network Flow

```
Browser (localhost:8000)          Browser (CloudFront URL)
     │                                    │
     │                                    │
     ▼                                    ▼
FastAPI Server                    CloudFront (S3)
(local computation)               (static files)
     │                                    │
     │                                    │
     ▼                                    ▼
Local Ollama                      API Gateway
(local LLM)                       (routing)
     │                                    │
     │                                    │
     ▼                                    ▼
                                  Lambda Functions
                                  (cloud computation)
                                       │
                                       │
                                       ▼
                                  DynamoDB
                                  (cloud storage)
```

## 🔍 Key Differences: Local vs AWS

### Local Development (`localhost:8000`)
- **Frontend**: Served by FastAPI (same server)
- **Backend**: FastAPI (Python) running locally
- **LLM**: Ollama running locally on your machine
- **Database**: DynamoDB in AWS (or local DynamoDB)
- **Auth**: Cognito in AWS

**Computation**: Happens on your local machine (FastAPI + Ollama)

### AWS Deployment (CloudFront URL)
- **Frontend**: CloudFront → S3 (static files)
- **Backend**: API Gateway → Lambda functions
- **LLM**: Lambda calls Ollama/HuggingFace APIs
- **Database**: DynamoDB in AWS
- **Auth**: Cognito in AWS

**Computation**: Happens in AWS Lambda (serverless functions)

## 📝 Important Notes

1. **All computation happens in Lambda** - The browser JavaScript just makes API calls
2. **CloudFront only serves static files** - No server-side processing
3. **API Gateway is just a router** - It doesn't execute code, just routes requests
4. **Lambda functions are stateless** - Each request is independent
5. **DynamoDB stores all persistent data** - Games, users, game history

## 🚀 Performance Characteristics

- **Cold Start**: First Lambda invocation may take 1-3 seconds
- **Warm Start**: Subsequent invocations are fast (<100ms)
- **Concurrent Requests**: Lambda scales automatically
- **Cost**: Pay per request (very cheap for low traffic)

## 🔐 Security Flow

1. User authenticates via Cognito Hosted UI
2. Cognito returns JWT token
3. Browser stores token (session cookie)
4. JavaScript includes token in API requests
5. Lambda validates token with Cognito
6. Lambda processes request if authorized

All authentication happens in the cloud (Cognito + Lambda), not in the browser!





