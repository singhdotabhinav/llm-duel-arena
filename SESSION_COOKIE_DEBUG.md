# Session Cookie Debugging Guide

## Current Issue: "Session state not found"

This error means the session cookie isn't being maintained between:
1. Redirect to Cognito (`/auth/login`)
2. Callback from Cognito (`/auth/callback`)

## Quick Debug Steps

### 1. Check Session Cookie in Browser

1. Open browser DevTools (F12)
2. Go to **Application** tab (Chrome) or **Storage** tab (Firefox)
3. Click **Cookies** → `http://localhost:8000`
4. Look for a cookie named `session`
5. **If the cookie doesn't exist**, that's the problem!

### 2. Test Session Endpoint

Visit: `http://localhost:8000/auth/debug/session`

This will show:
- Whether session exists
- What keys are in session
- What cookies browser sent
- Cookie header value

### 3. Check Browser Settings

**Chrome:**
- Settings → Privacy and security → Cookies and other site data
- Ensure "Allow all cookies" or "Block third-party cookies" (not "Block all cookies")
- Check if localhost is blocked

**Firefox:**
- Settings → Privacy & Security → Cookies and Site Data
- Ensure cookies are not blocked

### 4. Clear Everything and Retry

```bash
# Stop your server
# Clear browser cookies for localhost:8000
# Restart server
# Try login again
```

### 5. Check Server Logs

After clicking "Sign In", check server logs for:
- `[Cognito OIDC] Session keys after redirect: ...`
- `[Cognito OIDC] Set-Cookie header: ...`

If `Set-Cookie header: Not set`, the session middleware isn't working.

## Common Causes

1. **Browser blocking cookies** (most common)
   - Solution: Enable cookies, don't use incognito mode

2. **APP_SECRET_KEY not set or changed**
   - Check `.env` file has `APP_SECRET_KEY=some-secret-value`
   - Must be consistent between requests

3. **SessionMiddleware not configured**
   - Check `app/main.py` has `SessionMiddleware` added
   - Must be added BEFORE routers

4. **SameSite cookie restrictions**
   - Currently set to `same_site="lax"` which should work
   - If still failing, try `same_site="none"` (requires HTTPS)

## Testing Steps

1. **Visit debug endpoint first:**
   ```
   http://localhost:8000/auth/debug/session
   ```
   Should show `session_keys: ['_session_init']` or similar

2. **Click Sign In:**
   - Should redirect to Cognito
   - Check browser cookies - should see `session` cookie

3. **After Cognito login:**
   - Should redirect back to `/auth/callback`
   - Check cookies again - `session` cookie should still exist
   - Check server logs for session keys

4. **If cookie disappears:**
   - Browser is blocking it
   - Check browser settings
   - Try different browser
   - Try normal (non-incognito) mode

## Next Steps

If session cookie is being set but still not working:
1. Share output from `/auth/debug/session` endpoint
2. Share browser DevTools → Application → Cookies screenshot
3. Share server logs from login attempt

