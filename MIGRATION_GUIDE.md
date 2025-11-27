# Migration Guide: FastAPI → Serverless (Lambda + DynamoDB)

This guide helps you migrate from the current FastAPI + SQLite setup to a serverless architecture using AWS Lambda, API Gateway, and DynamoDB.

## Overview

### Current Architecture
- FastAPI application (monolithic)
- SQLite database
- Local file storage
- Session-based authentication

### Target Architecture
- Lambda functions (serverless)
- DynamoDB (NoSQL)
- S3 + CloudFront (static assets)
- JWT-based authentication

## Step-by-Step Migration

### Phase 1: Database Migration (SQLite → DynamoDB)

#### 1.1 Understand DynamoDB Schema

**Single-Table Design** (cost-optimized):
```
PK: game_id (or user_id)
SK: move_id (or 'metadata')
GSI: user-games-index (PK: user_id, SK: created_at)
```

**Table Structure:**
- Games: `game_id` + `move_id='metadata'` = game info
- Moves: `game_id` + `move_id='move_0001'` = individual moves
- Users: `game_id='user_xxx'` + `move_id='metadata'` = user info

#### 1.2 Migrate Existing Data

```python
# migration_script.py
import sqlite3
import boto3
import json
from datetime import datetime

# Connect to SQLite
sqlite_conn = sqlite3.connect('llm_duel_arena.db')
cursor = sqlite_conn.cursor()

# Connect to DynamoDB
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('llm-duel-arena-games-dev')

# Migrate games
cursor.execute('SELECT * FROM games')
games = cursor.fetchall()

for game in games:
    item = {
        'game_id': game[0],  # id
        'move_id': 'metadata',
        'user_id': game[1] or 'anonymous',  # user_id
        'game_type': game[2],  # game_type
        'white_model': game[3] or '',
        'black_model': game[4] or '',
        'result': game[5] or '',
        'winner': game[6],
        'moves_count': game[7] or 0,
        'is_over': game[8] or 0,
        'white_tokens': game[9] or 0,
        'black_tokens': game[10] or 0,
        'created_at': game[11].isoformat() if game[11] else datetime.utcnow().isoformat(),
        'updated_at': game[12].isoformat() if game[12] else datetime.utcnow().isoformat(),
        'game_state': game[13] or '{}',
        'ttl': int(datetime.utcnow().timestamp()) + (30 * 24 * 60 * 60)
    }
    table.put_item(Item=item)

# Migrate users
cursor.execute('SELECT * FROM users')
users = cursor.fetchall()

for user in users:
    item = {
        'game_id': f"user_{user[0]}",  # id
        'move_id': 'metadata',
        'user_id': user[0],
        'email': user[1],
        'name': user[2] or '',
        'picture': user[3] or '',
        'created_at': user[4].isoformat() if user[4] else datetime.utcnow().isoformat(),
        'last_login': user[5].isoformat() if user[5] else datetime.utcnow().isoformat(),
        'ttl': int(datetime.utcnow().timestamp()) + (365 * 24 * 60 * 60)
    }
    table.put_item(Item=item)

print("Migration complete!")
```

### Phase 2: Code Refactoring

#### 2.1 Update Imports

**Before (FastAPI):**
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
```

**After (Lambda):**
```python
from services.dynamodb_service import save_game_to_db, get_game_from_db
```

#### 2.2 Update Database Calls

**Before:**
```python
def save_game_to_db(game_state, user_id=None):
    db = SessionLocal()
    game = db.query(Game).filter(Game.id == game_state.game_id).first()
    # ... SQLAlchemy operations
```

**After:**
```python
def save_game_to_db(game_state, user_id=None):
    return dynamodb_service.save_game_to_db(game_state, user_id)
```

#### 2.3 Update Route Handlers

**Before (FastAPI):**
```python
@router.post("/games")
async def create_game(req: CreateGameRequest, db: Session = Depends(get_db)):
    state = game_manager.create_game(req.game_type, req.white_model, req.black_model)
    save_game_to_db(state, user.id)
    return state
```

**After (Lambda):**
```python
def lambda_handler(event, context):
    body = json.loads(event.get('body', '{}'))
    state = game_manager.create_game(body['game_type'], ...)
    save_game_to_db(state, user_id)
    return {
        'statusCode': 200,
        'body': json.dumps({'game_id': state.game_id})
    }
```

### Phase 3: Authentication Changes

#### 3.1 Session → JWT

**Before:**
- Server-side sessions (cookies)
- In-memory session store

**After:**
- JWT tokens (stateless)
- Client stores token in localStorage
- Token in Authorization header

#### 3.2 Update Auth Flow

1. User clicks "Sign in with Google"
2. Lambda returns OAuth URL
3. Client redirects to Google
4. Google redirects back with code
5. Client exchanges code for JWT (via Lambda)
6. Client stores JWT in localStorage
7. Client sends JWT in Authorization header for API calls

### Phase 4: Frontend Updates

#### 4.1 Update API Endpoints

**Before:**
```javascript
const response = await fetch('/api/games', {
  method: 'POST',
  body: JSON.stringify(data)
});
```

**After:**
```javascript
const apiUrl = 'https://your-api-id.execute-api.us-east-1.amazonaws.com';
const response = await fetch(`${apiUrl}/api/games`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('jwt_token')}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(data)
});
```

#### 4.2 Update Environment Variables

Create `.env.production`:
```
VITE_API_URL=https://your-api-id.execute-api.us-east-1.amazonaws.com
VITE_CLOUDFRONT_URL=https://d1234567890.cloudfront.net
```

### Phase 5: Deployment

#### 5.1 Build Lambda Packages

```bash
cd infrastructure
./deploy.sh dev us-east-1
```

#### 5.2 Deploy Static Assets

```bash
# Build frontend
npm run build

# Upload to S3
aws s3 sync dist/ s3://llm-duel-arena-static-dev-ACCOUNT_ID/

# Invalidate CloudFront cache
aws cloudfront create-invalidation \
  --distribution-id E1234567890 \
  --paths "/*"
```

## Testing Checklist

- [ ] Lambda functions deploy successfully
- [ ] API Gateway routes work
- [ ] DynamoDB queries return correct data
- [ ] Authentication flow works
- [ ] Game creation works
- [ ] Game moves work
- [ ] LLM calls work
- [ ] Static assets load from CloudFront
- [ ] CORS headers are correct
- [ ] Error handling works

## Rollback Plan

If something goes wrong:

1. **Keep FastAPI running** until Lambda is fully tested
2. **Use feature flags** to switch between old/new API
3. **Database**: Keep SQLite as backup, sync to DynamoDB
4. **Gradual migration**: Migrate one endpoint at a time

## Cost Monitoring

Set up CloudWatch alarms:
- Lambda invocations > 1M/month (free tier limit)
- DynamoDB read/write units > free tier
- API Gateway requests > 1M/month

## Next Steps

1. ✅ Terraform infrastructure created
2. ✅ DynamoDB service layer created
3. ✅ Lambda handlers created
4. ⏳ Test Lambda functions locally
5. ⏳ Deploy to dev environment
6. ⏳ Migrate existing data
7. ⏳ Update frontend
8. ⏳ Deploy to production

## Resources

- [AWS Lambda Python Guide](https://docs.aws.amazon.com/lambda/latest/dg/lambda-python.html)
- [DynamoDB Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)
- [API Gateway HTTP API](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api.html)







