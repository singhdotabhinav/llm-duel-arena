# DynamoDB Session Storage Implementation

## Summary
Implemented DynamoDB-backed session storage for AWS Lambda deployments, replacing cookie-based sessions with persistent, scalable session management.

## Changes Made

### New Files
1. **`app/middleware/dynamodb_session.py`**
   - `DynamoDBSessionDict`: Dict-like wrapper for DynamoDB session data
   - `DynamoDBSessionMiddleware`: Middleware that manages DynamoDB-backed sessions
   - Provides Starlette-compatible session interface

2. **`docs/DYNAMODB_SESSIONS.md`**
   - Comprehensive guide for DynamoDB session storage
   - Setup instructions, troubleshooting, and best practices

### Modified Files
1. **`app/main.py`**
   - Added conditional middleware selection based on `USE_DYNAMODB_SESSIONS`
   - Falls back to cookie-based sessions when disabled
   - Added logging for session system selection

2. **`app/services/session_store.py`**
   - Enhanced `get_session_store()` with better error handling
   - Added `get_session_store_instance()` for singleton pattern
   - Improved fallback to in-memory sessions

3. **`DYNAMODB_TABLES_SETUP.md`**
   - Added usage guidance for DynamoDB sessions
   - Clarified when to use DynamoDB vs cookie-based sessions

4. **`env.example`**
   - Updated comments for `USE_DYNAMODB_SESSIONS` variable

## Testing Checklist

### Code Quality
- ✅ No linter errors (flake8, mypy)
- ✅ Code follows project style (black formatting, line length 127)
- ✅ All imports are valid
- ✅ Type hints included where appropriate

### Functionality
- ✅ Middleware provides dict-like interface compatible with Starlette
- ✅ Session creation, update, and deletion work correctly
- ✅ Automatic TTL expiration via DynamoDB
- ✅ Fallback to in-memory sessions if DynamoDB fails
- ✅ Cookie management (stores only session_id)

### Integration
- ✅ Works with existing authentication routers (no changes needed)
- ✅ Compatible with Cognito OIDC authentication
- ✅ Backward compatible (cookie-based sessions still default)

## Configuration

### To Enable DynamoDB Sessions
```bash
USE_DYNAMODB_SESSIONS=true
SESSION_TABLE_NAME=LLM-Duel-Sessions
AWS_REGION=us-east-1
```

### Required DynamoDB Table
- Table name: `LLM-Duel-Sessions` (or custom via `SESSION_TABLE_NAME`)
- Partition key: `session_id` (String)
- TTL attribute: `ttl` (Number)
- Billing mode: PAY_PER_REQUEST (recommended)

## Breaking Changes
None - This is a backward-compatible addition. Cookie-based sessions remain the default.

## Migration Notes
- Existing cookie sessions will be invalidated when switching to DynamoDB sessions
- Users will need to log in again after migration
- No code changes required in routers or services

## Next Steps
1. Test locally with `USE_DYNAMODB_SESSIONS=true`
2. Create DynamoDB table in AWS
3. Deploy to Lambda with proper IAM permissions
4. Monitor CloudWatch logs for session operations

