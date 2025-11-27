# AWS Credentials Note

## Important: OAuth Flow Doesn't Need AWS Credentials!

The **OAuth flow** (Hosted UI login) you're using **does NOT require AWS credentials**. It's completely browser-based:

- ✅ Uses `authlib` library
- ✅ Browser redirects to Cognito
- ✅ No boto3 calls
- ✅ No AWS credentials needed

The AWS credentials you see in logs are only used if you use the **programmatic API endpoints** (`/api/auth/signup`, `/api/auth/login`).

## Current Setup

You're using:
- **OAuth flow** (`/auth/login`) → No AWS credentials needed ✅
- **Programmatic API** (`/api/auth/*`) → Uses boto3, needs AWS credentials

## If You Need Different AWS Profile

If you want to use a different AWS profile for the programmatic API (not needed for OAuth), add to your `.env`:

```bash
# Optional: Use specific AWS profile for boto3 calls
AWS_PROFILE=your-personal-profile-name
```

Then configure your `~/.aws/credentials`:

```ini
[default]
# Company credentials (currently being used)

[your-personal-profile-name]
aws_access_key_id = YOUR_PERSONAL_ACCESS_KEY
aws_secret_access_key = YOUR_PERSONAL_SECRET_KEY
region = eu-north-1
```

## For OAuth Flow (What You're Using)

**You don't need to change anything!** The OAuth flow works independently of AWS credentials.

The `mismatching_state` error is about **session cookies**, not AWS credentials.

## Summary

- ✅ **OAuth login** (`/auth/login`) → Works without AWS credentials
- ⚠️ **Programmatic API** (`/api/auth/signup`) → Needs AWS credentials (only if you use those endpoints)
- 🔧 **Current issue** → Session cookies, not AWS credentials

