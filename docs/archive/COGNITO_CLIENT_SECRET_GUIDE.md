# AWS Cognito Client Secret Guide

## Important: Do You Need a Client Secret?

**For web applications using OAuth/OIDC flows, you typically DO NOT need a client secret.**

### Why?
- Client secrets cannot be securely stored in browser JavaScript
- OAuth 2.0 Authorization Code flow with PKCE (Proof Key for Code Exchange) doesn't require secrets
- Cognito Hosted UI works fine without a client secret for web apps

### When You Might Need a Client Secret:
- Server-to-server authentication
- Mobile apps (native apps)
- Backend API authentication

## Current Setup (No Client Secret - Recommended)

Your current code already handles the case where `client_secret` is empty:

```python
client_secret=settings.cognito_client_secret if settings.cognito_client_secret else None
```

**Your `.env` should have:**
```bash
COGNITO_CLIENT_SECRET=  # Leave empty - this is correct!
```

## How to Check if Your App Client Has a Secret

1. **Go to AWS Cognito Console**
   - Navigate to your User Pool
   - Go to "App integration" tab
   - Click on your App Client

2. **Check App Client Details**
   - Look for "Client secret" field
   - If it shows "Not available" or is blank → No secret (this is fine!)
   - If it shows a value → You have a secret

## How to Generate a Client Secret (If Needed)

**⚠️ Warning:** If your app client was created WITHOUT a secret, you CANNOT add one later. You must create a NEW app client.

### Option 1: Create New App Client WITH Secret

1. **Go to Cognito User Pool → App Integration**
2. **Click "Create app client"**
3. **Fill in details:**
   - App client name: `llm-duel-arena-client-secure`
   - **IMPORTANT:** Check "Generate client secret" ✅
   - Authentication flows: Select "Authorization code grant"
   - OAuth 2.0 scopes: Select "openid", "email", "profile"
4. **Click "Create app client"**
5. **Copy the Client ID and Client Secret** (secret is only shown once!)
6. **Update your `.env`:**
   ```bash
   COGNITO_CLIENT_ID=new_client_id_here
   COGNITO_CLIENT_SECRET=new_client_secret_here
   ```
7. **Update Callback URLs** in the new app client settings

### Option 2: Use Existing App Client (No Secret - Recommended)

**Keep your current setup** - it works perfectly fine without a secret!

Your `.env`:
```bash
COGNITO_CLIENT_SECRET=  # Empty is correct!
```

## Troubleshooting

### Error: "Invalid client secret"
- If you're getting this error, check:
  1. Is `COGNITO_CLIENT_SECRET` set in `.env`?
  2. If your app client has NO secret, make sure `COGNITO_CLIENT_SECRET` is empty
  3. If your app client HAS a secret, make sure `COGNITO_CLIENT_SECRET` matches exactly

### Error: "Client authentication failed"
- This usually means:
  - You're trying to use a secret when the app client doesn't have one
  - OR you're not providing a secret when the app client requires one

## Recommended Configuration

**For web applications (your use case):**

```bash
# .env file
USE_COGNITO=true
COGNITO_USER_POOL_ID=eu-north-1_6WUbLC1KS
COGNITO_CLIENT_ID=371gt7emopsic4tqut8o5s4qep
COGNITO_CLIENT_SECRET=  # Leave empty - no secret needed!
COGNITO_REGION=eu-north-1
COGNITO_CALLBACK_URL=http://localhost:8000/auth/callback
```

**Code handles this automatically:**
```python
client_secret=settings.cognito_client_secret if settings.cognito_client_secret else None
```

## Verification

To verify your setup is correct:

1. **Check your App Client in AWS Console:**
   - Client secret should be "Not available" (for web apps)
   - OR you should have copied it if you created one with secret

2. **Check your `.env` file:**
   - If app client has NO secret → `COGNITO_CLIENT_SECRET=` (empty)
   - If app client HAS secret → `COGNITO_CLIENT_SECRET=your_secret_here`

3. **Test the login:**
   - Click "Sign In with Cognito"
   - Should redirect to Cognito Hosted UI
   - After login, should redirect back successfully

## Summary

**For your web application:**
- ✅ **No client secret needed** - Leave `COGNITO_CLIENT_SECRET` empty
- ✅ Your current code already handles this correctly
- ✅ OAuth flow works perfectly without a secret

**Only create a secret if:**
- You're doing server-to-server authentication
- You're building a mobile native app
- AWS requires it for your specific use case

