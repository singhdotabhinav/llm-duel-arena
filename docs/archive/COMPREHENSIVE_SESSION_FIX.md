# Comprehensive Session Cookie Fix

## Root Cause Analysis

The session cookie is being **set** but **not sent back** by the browser. This happens because:

1. **Cookie is set** when redirecting to Cognito (`/auth/login`)
2. **Cookie exists** in browser DevTools
3. **Cookie is NOT sent** when Cognito redirects back (`/auth/callback`)
4. **Result:** Session state is lost → "Session state not found" error

## The Fix

### 1. Ensure Session Cookie is Set Correctly

The code now:
- ✅ Initializes session before redirect
- ✅ Modifies session to trigger cookie setting
- ✅ Logs session state at each step
- ✅ Returns original authlib response (don't create new RedirectResponse)

### 2. Verify Cookie Attributes

**Check in Chrome DevTools → Application → Cookies → `localhost:8000`:**

The `session` cookie should have:
- **Domain:** `localhost` (or empty/not set)
- **Path:** `/`
- **SameSite:** `Lax`
- **HttpOnly:** ✓ (checked)
- **Secure:** ✗ (unchecked, for HTTP)

### 3. Test the Flow

1. **Clear ALL cookies** for `localhost:8000`
2. **Restart server** (to pick up code changes)
3. **Click "Sign In"**
4. **Check Network tab** → Response Headers → `Set-Cookie` header
   - Should see: `Set-Cookie: session=...; Path=/; Max-Age=3600; HttpOnly; SameSite=lax`
5. **Check Application tab** → Cookies → `session` cookie should exist
6. **After Cognito redirects back**, check Network tab → Request Headers → `Cookie` header
   - Should see: `Cookie: session=...`

## If Cookie Still Not Sent

### Check 1: Browser Console

Open Chrome DevTools → Console and check for:
- Cookie warnings
- Security errors
- CORS errors

### Check 2: Network Tab Details

1. Open Network tab
2. Click on `/auth/login` request
3. Check **Response Headers** → `Set-Cookie`
4. Click on `/auth/callback` request  
5. Check **Request Headers** → `Cookie`

### Check 3: Cookie Attributes

If cookie exists but isn't sent:
- **Domain mismatch:** Cookie set for `127.0.0.1` but accessing `localhost`
- **Path mismatch:** Cookie path doesn't match request path
- **SameSite blocking:** Browser blocking cookie due to SameSite policy

### Check 4: Server Logs

After clicking Sign In, check server logs for:
```
[Cognito OIDC] ===== COOKIE DEBUG =====
[Cognito OIDC] Cookies received: {...}
[Cognito OIDC] Cookie header: ...
```

If `Cookies received: {}` and `Cookie header: Not present`, the browser isn't sending the cookie.

## Common Solutions

### Solution 1: Use `localhost` Consistently

**Always access via:** `http://localhost:8000` (not `127.0.0.1`)

### Solution 2: Clear Cookies and Retry

1. Clear ALL cookies for `localhost:8000`
2. Restart server
3. Try login again

### Solution 3: Check Browser Settings

**Chrome:**
- Settings → Privacy and security → Cookies and other site data
- Ensure "Allow all cookies" or "Block third-party cookies" (not "Block all cookies")

### Solution 4: Try Incognito Mode

Test in incognito mode to rule out extensions blocking cookies.

## Debugging Steps

1. **Visit:** `http://localhost:8000/auth/debug/session`
2. **Check response:** Should set `session` cookie
3. **Visit again:** Cookie should be sent back
4. **If cookie not sent:** Check cookie attributes in DevTools

## Expected Behavior

**Before redirect to Cognito:**
- Session cookie is set
- Cookie appears in DevTools
- `Set-Cookie` header in response

**After Cognito redirects back:**
- Session cookie is sent back
- Cookie appears in request headers
- Session state is found
- Login succeeds

## If Still Not Working

Share:
1. **Server logs** from clicking Sign In (especially `[Cognito OIDC] ===== COOKIE DEBUG =====`)
2. **Network tab** screenshot showing:
   - `/auth/login` Response Headers → `Set-Cookie`
   - `/auth/callback` Request Headers → `Cookie`
3. **Application tab** → Cookies → `session` cookie attributes

This will help identify the exact issue.







