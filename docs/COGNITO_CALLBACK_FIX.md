# Fix Cognito Callback URL Error

## Common Error

If you see an error like:
- "redirect_uri_mismatch"
- "Invalid redirect URI"
- "The redirect URI provided does not match a registered redirect URI"

This means the callback URL isn't configured in your Cognito App Client.

## Quick Fix (2 Minutes)

### Step 1: Go to Cognito Console

1. Open AWS Console → Cognito → User Pools
2. Click on your user pool: `us-east-1_7fscSPSUe`
3. Go to **"App integration"** tab
4. Scroll to **"App clients"** section
5. Click on your app client (e.g., `2v96lg57eesiuln067hh5mgol9`)

### Step 2: Add Callback URL

1. Scroll to **"Hosted UI"** section
2. Find **"Allowed callback URLs"**
3. Click **"Edit"**
4. Add this EXACT URL:
   ```
   http://localhost:8000/auth/callback
   ```
5. Click **"Save changes"**

### Step 3: Verify Sign-Out URL

1. In the same section, find **"Allowed sign-out URLs"**
2. Make sure it includes:
   ```
   http://localhost:8000/
   ```
3. If not, add it and save

### Step 4: Verify OAuth Settings

Make sure these are enabled:
- ✅ **Authorization code grant**
- ✅ **OpenID Connect scopes**: `openid`, `email`, `profile`

## Complete Configuration Checklist

Your Cognito App Client should have:

**Allowed callback URLs:**
```
http://localhost:8000/auth/callback
https://d84l1y8p4kdic.cloudfront.net/auth/callback  (for production)
```

**Allowed sign-out URLs:**
```
http://localhost:8000/
https://d84l1y8p4kdic.cloudfront.net/  (for production)
```

**OAuth 2.0 grant types:**
- ✅ Authorization code grant
- ✅ Implicit grant (optional)

**OpenID Connect scopes:**
- ✅ openid
- ✅ email
- ✅ profile

## Test After Fix

1. Restart your local server (if running)
2. Go to http://localhost:8000
3. Click "Login" or "Sign Up"
4. You should be redirected to Cognito Hosted UI
5. After login, you should be redirected back to `http://localhost:8000/auth/callback`
6. You should be logged in!

## Still Getting Errors?

### Error: "redirect_uri_mismatch"

- Double-check the URL is EXACTLY: `http://localhost:8000/auth/callback`
- No trailing slash
- Use `localhost` not `127.0.0.1`
- Make sure you saved the changes

### Error: "Invalid client"

- Verify your `COGNITO_CLIENT_ID` in `.env` matches the App Client ID
- Check that the App Client is in the correct User Pool

### Error: "Invalid scope"

- Make sure OAuth scopes in Cognito include: `openid email profile`
- Check your `.env` has: `COGNITO_SCOPES=openid email profile`

## Quick Verification

After updating Cognito, test the callback URL directly:

```
https://us-east-17fscspsue.auth.us-east-1.amazoncognito.com/login?client_id=2v96lg57eesiuln067hh5mgol9&response_type=code&redirect_uri=http://localhost:8000/auth/callback&scope=openid+email+profile
```

If this works, Cognito is configured correctly!





