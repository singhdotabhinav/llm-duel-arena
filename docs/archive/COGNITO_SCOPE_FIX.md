# Fixing "invalid_scope" Error in Cognito

## Error Message
```
OAuthError: invalid_request: invalid_scope
```

## Cause
The scopes requested (`openid email profile`) are not enabled in your Cognito App Client configuration.

## Solution: Enable Scopes in Cognito

### Step 1: Go to Cognito App Client Settings

1. **AWS Console** → **Cognito** → **User Pools**
2. Select your user pool
3. Go to **"App integration"** tab
4. Click on your **App Client** (e.g., `llm-duel-arena-client`)

### Step 2: Configure OAuth Scopes

1. Scroll down to **"Hosted UI"** section
2. Under **"Allowed OAuth scopes"**, check these boxes:
   - ✅ **openid** (required for OIDC)
   - ✅ **email** (to get user email)
   - ✅ **profile** (to get user name/profile info)
3. Click **"Save changes"**

### Step 3: Verify OAuth Flows

Make sure these are also configured:
- **Allowed OAuth flows**: 
  - ✅ **Authorization code grant** (required)
- **Allowed callback URLs**:
  - `http://localhost:8000/auth/callback`
- **Allowed sign-out URLs**:
  - `http://localhost:8000/`

### Step 4: Restart Your Application

After making changes in Cognito:
```bash
# Stop your server (Ctrl+C)
# Restart
uvicorn app.main:app --reload
```

## Alternative: Use Different Scopes

If you want to use different scopes, you can modify the code:

**In `app/routers/cognito_oidc_auth.py`:**

```python
'client_kwargs': {
    'scope': 'openid email'  # Only openid and email
},
```

And update the login route:
```python
return await oauth.cognito.authorize_redirect(
    request, 
    redirect_uri,
    scope='openid email'  # Match the scopes above
)
```

**But make sure these scopes are enabled in Cognito App Client settings!**

## Verification Checklist

✅ **Cognito App Client Settings:**
- [ ] `openid` scope is enabled
- [ ] `email` scope is enabled  
- [ ] `profile` scope is enabled
- [ ] Authorization code grant flow is enabled
- [ ] Callback URL is configured: `http://localhost:8000/auth/callback`

✅ **Code Configuration:**
- [ ] `client_kwargs` has `scope: 'openid email profile'`
- [ ] `authorize_redirect` uses the same scope
- [ ] `.env` has correct `COGNITO_CLIENT_ID`

## Common Issues

### Issue 1: Scopes not enabled
**Symptom:** `invalid_scope` error
**Fix:** Enable the scopes in Cognito App Client settings (see Step 2 above)

### Issue 2: Scope mismatch
**Symptom:** Works sometimes, fails other times
**Fix:** Ensure the scope in code matches what's enabled in Cognito

### Issue 3: Callback URL not configured
**Symptom:** Redirect fails after Cognito login
**Fix:** Add `http://localhost:8000/auth/callback` to allowed callback URLs

## Quick Fix Summary

1. Go to Cognito → Your User Pool → App Client
2. Enable scopes: `openid`, `email`, `profile`
3. Save changes
4. Restart your application
5. Try login again

The error should be resolved!

