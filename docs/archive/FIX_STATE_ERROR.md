# Fix: mismatching_state Error

## The Problem
You're getting: `mismatching_state: CSRF Warning! State not equal in request and response`

This happens when the OAuth state parameter stored in your session doesn't match the state returned from Cognito.

## Common Causes

1. **Session cookies not being maintained** - Browser blocking cookies
2. **APP_SECRET_KEY changed** - Session can't be decrypted
3. **Using incognito/private mode** - Cookies cleared between redirects
4. **Session middleware not configured properly**

## Quick Fixes

### Fix 1: Check APP_SECRET_KEY

Make sure your `.env` has a consistent `APP_SECRET_KEY`:

```bash
# Generate a secure random key (32+ characters)
APP_SECRET_KEY=your-secure-random-key-here-minimum-32-characters
```

**Important:** Don't change this key between requests! If you change it, all existing sessions become invalid.

### Fix 2: Enable Cookies in Browser

1. **Chrome/Edge:**
   - Settings → Privacy and security → Cookies
   - Ensure "Allow all cookies" or "Block third-party cookies" (but allow first-party)

2. **Firefox:**
   - Settings → Privacy & Security
   - Under "Cookies and Site Data", select "Accept cookies and site data"

3. **Safari:**
   - Preferences → Privacy
   - Uncheck "Prevent cross-site tracking"

### Fix 3: Don't Use Incognito/Private Mode

OAuth flows require cookies to maintain state. Incognito/private mode may clear cookies between redirects.

### Fix 4: Clear Browser Data and Retry

1. Clear cookies for `localhost:8000`
2. Clear cookies for your Cognito domain
3. Restart your application
4. Try login again

### Fix 5: Check Session Middleware Configuration

Ensure `SessionMiddleware` is added **BEFORE** routers in `main.py`:

```python
app = FastAPI(title=settings.app_name)

# SessionMiddleware MUST be added first
app.add_middleware(SessionMiddleware, ...)

# Then add routers
app.include_router(...)
```

## Debugging Steps

1. **Check server logs** - Look for session state keys
2. **Check browser DevTools:**
   - Application → Cookies → `localhost:8000`
   - Should see a `session` cookie
3. **Verify APP_SECRET_KEY:**
   ```bash
   # In your .env file, make sure it's set:
   APP_SECRET_KEY=some-long-random-string
   ```

## Test the Fix

1. **Clear all cookies** for localhost
2. **Restart your application**
3. **Open in normal browsing mode** (not incognito)
4. **Try login again**

## If Still Not Working

Try this workaround - disable state verification temporarily (NOT recommended for production):

```python
# In cognito_oidc_auth.py, modify authorize_access_token call:
# This is a temporary workaround - not secure for production!
token = await oauth.cognito.authorize_access_token(
    request,
    state=None  # Disable state verification (NOT SECURE!)
)
```

**Warning:** Only use this for testing! It disables CSRF protection.

## Production Checklist

- [ ] `APP_SECRET_KEY` is set and consistent
- [ ] Session middleware configured correctly
- [ ] Cookies enabled in browser
- [ ] Not using incognito mode
- [ ] HTTPS enabled (for production)
- [ ] `same_site="lax"` or `same_site="none"` with `secure=True`

