# Troubleshooting "Something went wrong" Error

## This Error Usually Means:

The error "Something went wrong" from Cognito Hosted UI typically indicates a **configuration mismatch** between:
- What your app is sending to Cognito
- What Cognito expects

## Step-by-Step Debugging:

### 1. Check Server Logs

Look for these log entries when you click "Sign In":

```
[Cognito OIDC] Redirecting to Cognito for login. Callback: ...
[Cognito OIDC] Request hostname: ...
[Cognito OIDC] Callback received with params: ...
```

**Share these logs** - they'll show what's happening.

### 2. Verify Cognito App Client Settings

Go to AWS Console → Cognito → User Pool → App Client:

**Check these settings:**

1. **Allowed callback URLs:**
   ```
   http://localhost:8000/auth/callback
   ```
   - Must be EXACTLY this (no trailing slash, no extra paths)
   - Must use `localhost` (not `127.0.0.1`)

2. **Allowed sign-out URLs:**
   ```
   http://localhost:8000/
   ```

3. **Allowed OAuth scopes:**
   - ✅ `openid`
   - ✅ `email`
   - ✅ `profile`

4. **Allowed OAuth flows:**
   - ✅ `Authorization code grant`
   - ✅ `Implicit grant` (optional)

### 3. Check Your `.env` File

Make sure these match:

```bash
COGNITO_CALLBACK_URL=http://localhost:8000/auth/callback
COGNITO_LOGOUT_URL=http://localhost:8000/
COGNITO_CLIENT_ID=your_client_id_here
COGNITO_USER_POOL_ID=your_pool_id_here
COGNITO_REGION=your_region_here
COGNITO_DOMAIN=your_domain_here
```

### 4. Common Issues:

#### Issue 1: Callback URL Mismatch
**Symptom:** Error happens immediately when clicking Sign In

**Fix:**
- Ensure Cognito callback URL is EXACTLY: `http://localhost:8000/auth/callback`
- No trailing slash, no extra characters
- Must use `localhost` (not `127.0.0.1`)

#### Issue 2: Missing Scopes
**Symptom:** Error after login, before callback

**Fix:**
- Enable `openid`, `email`, `profile` in Cognito App Client
- Check server logs for "invalid_scope" error

#### Issue 3: Domain Not Configured
**Symptom:** Can't reach Cognito Hosted UI

**Fix:**
- Ensure `COGNITO_DOMAIN` is set in `.env`
- Format: `your-domain` (without `.auth.region.amazoncognito.com`)

### 5. Test the Flow:

1. **Clear browser cookies** for `localhost:8000`
2. **Restart your server**
3. **Click "Sign In"**
4. **Check server logs** - look for:
   - What callback URL is being used
   - Any errors in the logs
   - What parameters Cognito sends back

### 6. Check Browser Console

Open DevTools → Console and look for:
- Any JavaScript errors
- Network errors
- Redirect issues

### 7. Verify Cognito Domain

Make sure your Cognito domain is accessible:
- Go to Cognito → User Pool → App integration → Domain
- Test the domain URL in browser
- Should show Cognito login page

## What to Share:

If still having issues, share:

1. **Server logs** (especially lines starting with `[Cognito OIDC]`)
2. **Browser console errors** (if any)
3. **Cognito App Client settings** (screenshot or list):
   - Allowed callback URLs
   - Allowed OAuth scopes
   - OAuth flows enabled
4. **Your `.env` file** (with sensitive values redacted):
   - `COGNITO_CALLBACK_URL=...`
   - `COGNITO_CLIENT_ID=...`
   - `COGNITO_USER_POOL_ID=...`
   - `COGNITO_DOMAIN=...`

## Quick Checklist:

- [ ] Callback URL in Cognito: `http://localhost:8000/auth/callback`
- [ ] Callback URL in `.env`: `http://localhost:8000/auth/callback`
- [ ] Scopes enabled: `openid`, `email`, `profile`
- [ ] OAuth flow: `Authorization code grant`
- [ ] Cognito domain configured and accessible
- [ ] Server restarted after changes
- [ ] Browser cookies cleared








