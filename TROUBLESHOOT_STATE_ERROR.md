# Troubleshooting: CSRF State Verification Failed

## Your APP_SECRET_KEY is ✅ Set Correctly

The diagnostic shows your `APP_SECRET_KEY` is properly configured (86 characters).

## The Real Issue: Session Cookies Not Maintained

The `mismatching_state` error means the session cookie isn't being maintained between:
1. When you click "Sign In" → State stored in session → Redirect to Cognito
2. Cognito redirects back → Session should have state → But it's empty!

## Step-by-Step Fix

### Step 1: Check Browser Cookies

1. **Open Browser DevTools** (F12 or Cmd+Option+I)
2. Go to **Application** tab (Chrome) or **Storage** tab (Firefox)
3. Click **Cookies** → `http://localhost:8000`
4. **Look for a cookie named `session`**

**If the cookie doesn't exist:**
- Cookies are being blocked
- Session middleware isn't setting cookies properly

**If the cookie exists:**
- Check its value (should be encrypted)
- Check if it persists after redirect

### Step 2: Clear Everything and Retry

1. **Clear ALL cookies for localhost:8000:**
   - DevTools → Application → Cookies → localhost:8000
   - Right-click → Clear
   
2. **Clear cookies for Cognito domain:**
   - Look for cookies from `*.amazoncognito.com` or `*.auth.eu-north-1.amazoncognito.com`
   - Clear those too

3. **Restart your application:**
   ```bash
   # Stop server (Ctrl+C)
   uvicorn app.main:app --reload
   ```

4. **Try login again** in a fresh browser session

### Step 3: Check Browser Settings

**Chrome/Edge:**
- Settings → Privacy and security → Cookies and other site data
- Ensure "Allow all cookies" OR "Block third-party cookies" (but allow first-party)
- Make sure `localhost` is not blocked

**Firefox:**
- Settings → Privacy & Security
- Under "Cookies and Site Data", select "Accept cookies and site data"

**Safari:**
- Preferences → Privacy
- Uncheck "Prevent cross-site tracking"
- Ensure cookies are enabled

### Step 4: Don't Use Incognito/Private Mode

OAuth flows **require** cookies to maintain state. Incognito/private mode often clears cookies between redirects, causing this error.

**Use normal browsing mode** for testing.

### Step 5: Check Server Logs

After clicking "Sign In", check your server logs. You should see:

```
[Cognito OIDC] Session keys after redirect: ['_state_cognito', ...]
```

If you see empty session keys `[]`, the session cookie isn't being set.

### Step 6: Verify Session Cookie in Response

1. Open DevTools → Network tab
2. Click "Sign In with Cognito"
3. Find the `/auth/login` request
4. Check **Response Headers**
5. Look for `Set-Cookie: session=...`

**If `Set-Cookie` is missing:**
- Session middleware isn't working
- Check `main.py` - SessionMiddleware should be added

## Quick Test

Try this in your browser console (after clicking Sign In):

```javascript
// Check if session cookie exists
document.cookie.split(';').find(c => c.trim().startsWith('session='))
```

If this returns `undefined`, cookies aren't being set.

## Alternative: Temporary Workaround (Testing Only)

If you need to test quickly, you can temporarily disable state verification:

**⚠️ WARNING: This disables CSRF protection - ONLY for local testing!**

In `app/routers/cognito_oidc_auth.py`, modify the callback:

```python
# TEMPORARY - NOT SECURE FOR PRODUCTION!
token = await oauth.cognito.authorize_access_token(request, state=None)
```

**Remove this after testing!**

## Most Likely Solution

Based on the error, try this:

1. **Close all browser tabs** for localhost:8000
2. **Clear browser cache and cookies** completely
3. **Restart your application server**
4. **Open a fresh browser window** (not incognito)
5. **Go to** `http://localhost:8000/`
6. **Click "Sign In with Cognito"**

The session cookie should now be properly maintained.

## Still Not Working?

Check these in order:

1. ✅ APP_SECRET_KEY is set (you've confirmed this)
2. ✅ SessionMiddleware is configured (check `main.py`)
3. ❓ Cookies enabled in browser
4. ❓ Not using incognito mode
5. ❓ Browser extensions blocking cookies
6. ❓ Firewall/antivirus blocking cookies

Let me know what you see in the browser DevTools → Application → Cookies after clicking Sign In!

