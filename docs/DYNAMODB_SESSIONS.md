# DynamoDB Session Storage Guide

## Overview

DynamoDB session storage provides persistent, scalable session management for the LLM Duel Arena application. This is especially important for AWS Lambda deployments where sessions need to persist across cold starts and be shared across multiple Lambda instances.

## Architecture

### Cookie-Based Sessions (Default)
```
Browser → Cookie (encrypted session data) → FastAPI reads cookie
```
- **Pros**: Simple, no database needed, works great for single-server deployments
- **Cons**: Cookie size limits, not shared across servers, lost on Lambda cold starts

### DynamoDB Sessions (When Enabled)
```
Browser → Cookie (session_id only) → FastAPI → DynamoDB (session data)
```
- **Pros**: Scalable, persistent, shared across instances, automatic expiration
- **Cons**: Requires DynamoDB table, slight latency increase

## Setup

### 1. Create DynamoDB Table

First, create the sessions table using the AWS CLI or Terraform:

```bash
aws dynamodb create-table \
  --table-name LLM-Duel-Sessions \
  --attribute-definitions AttributeName=session_id,AttributeType=S \
  --key-schema AttributeName=session_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1

# Enable TTL
aws dynamodb update-time-to-live \
  --table-name LLM-Duel-Sessions \
  --time-to-live-specification '{"Enabled":true,"AttributeName":"ttl"}' \
  --region us-east-1
```

Or use the Python script from `DYNAMODB_TABLES_SETUP.md`.

### 2. Configure Environment Variables

Add to your `.env` file:

```bash
# Enable DynamoDB sessions
USE_DYNAMODB_SESSIONS=true
SESSION_TABLE_NAME=LLM-Duel-Sessions
AWS_REGION=us-east-1

# AWS credentials (if not using IAM role)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
```

### 3. Verify Table Exists

```bash
aws dynamodb describe-table --table-name LLM-Duel-Sessions --region us-east-1
```

## How It Works

### Session Lifecycle

1. **Session Creation**: When a user logs in, a new session is created in DynamoDB with:
   - `session_id`: Unique identifier (stored in cookie)
   - `user_data`: JSON-encoded session data
   - `created_at`: Timestamp
   - `ttl`: Expiration timestamp (DynamoDB auto-deletes expired sessions)

2. **Session Retrieval**: On each request:
   - Middleware reads `session_id` from cookie
   - Loads session data from DynamoDB
   - Attaches session dict to `request.session`

3. **Session Updates**: When session data changes:
   - Middleware detects modification
   - Updates DynamoDB with new data
   - Extends TTL (sliding expiration)

4. **Session Deletion**: On logout:
   - Session deleted from DynamoDB
   - Cookie removed from browser

### Session Interface

The DynamoDB session middleware provides a dict-like interface compatible with Starlette's session:

```python
# Set session data
request.session["user"] = {"email": "user@example.com", "name": "User"}

# Get session data
user = request.session.get("user")

# Delete session data
request.session.pop("user", None)

# Clear entire session
request.session.clear()
```

## Configuration

### Session Duration

Default session duration is 1 hour (3600 seconds). This can be configured in `app/main.py`:

```python
app.add_middleware(
    DynamoDBSessionMiddleware,
    session_cookie="session_id",
    max_age=7200,  # 2 hours
)
```

### TTL Behavior

- Sessions automatically expire after `max_age` seconds
- TTL is extended on each session update (sliding expiration)
- DynamoDB automatically deletes expired sessions (within 48 hours)

## Local Development

For local development, you can:

1. **Use DynamoDB locally**: Set `USE_DYNAMODB_SESSIONS=true` and configure AWS credentials
2. **Use in-memory fallback**: Set `USE_DYNAMODB_SESSIONS=false` (default) - uses cookie-based sessions

The in-memory fallback is automatically used if DynamoDB initialization fails.

## AWS Lambda Deployment

When deploying to AWS Lambda:

1. **Required**: Set `USE_DYNAMODB_SESSIONS=true`
2. **IAM Permissions**: Lambda execution role needs DynamoDB permissions:
   ```json
   {
     "Effect": "Allow",
     "Action": [
       "dynamodb:GetItem",
       "dynamodb:PutItem",
       "dynamodb:UpdateItem",
       "dynamodb:DeleteItem"
     ],
     "Resource": "arn:aws:dynamodb:us-east-1:*:table/LLM-Duel-Sessions"
   }
   ```
3. **Environment Variables**: Set in Lambda configuration:
   - `USE_DYNAMODB_SESSIONS=true`
   - `SESSION_TABLE_NAME=LLM-Duel-Sessions`
   - `AWS_REGION=us-east-1`

## Troubleshooting

### Sessions Not Persisting

- Check DynamoDB table exists and is accessible
- Verify IAM permissions for DynamoDB access
- Check CloudWatch logs for DynamoDB errors
- Verify `USE_DYNAMODB_SESSIONS=true` is set

### Session Cookie Not Set

- Check browser console for cookie errors
- Verify CORS settings allow cookies
- Check `https_only` setting matches deployment (false for localhost, true for HTTPS)

### Sessions Expiring Too Quickly

- Check `max_age` setting in middleware configuration
- Verify TTL is being extended on session updates
- Check DynamoDB table TTL is enabled

### Fallback to In-Memory

If DynamoDB initialization fails, the middleware automatically falls back to in-memory sessions. Check logs for initialization errors.

## Cost Considerations

DynamoDB On-Demand pricing (as of 2024):
- **Write**: $1.25 per million write units
- **Read**: $0.25 per million read units
- **Storage**: $0.25 per GB-month

For typical usage:
- 1,000 active sessions = ~$0.01/month storage
- 10,000 session operations/day = ~$0.10/month

Very cost-effective for most applications!

## Migration from Cookie Sessions

To migrate from cookie-based to DynamoDB sessions:

1. Create DynamoDB table (see Setup section)
2. Set `USE_DYNAMODB_SESSIONS=true` in environment
3. Deploy updated code
4. Existing cookie sessions will be invalidated (users need to log in again)
5. New sessions will be stored in DynamoDB

No code changes needed - the session interface is identical!

