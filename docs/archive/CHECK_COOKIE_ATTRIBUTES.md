# Check Cookie Attributes

## Current Issue

Session cookie exists in browser but isn't being sent back in requests.

## What to Check

### 1. Cookie Attributes in DevTools

Go to Chrome DevTools → Application → Cookies → `http://localhost:8000`

Find the `session` cookie and check:

- **Name:** `session`
- **Value:** (should be a long encoded string)
- **Domain:** Should be `localhost` (NOT `127.0.0.1`)
- **Path:** Should be `/`
- **Expires / Max-Age:** Should show a future date
- **Size:** Should be a number (e.g., 702)
- **HttpOnly:** Should be checked ✓
- **Secure:** Should be unchecked (for HTTP)
- **SameSite:** Should be `Lax`

### 2. Network Tab - Response Headers

1. Open Chrome DevTools → Network tab
2. Visit: `http://localhost:8000/auth/debug/session`
3. Click on the request
4. Go to "Headers" tab
5. Scroll to "Response Headers"
6. Look for `Set-Cookie` header

**What to look for:**
```
Set-Cookie: session=...; Path=/; Max-Age=3600; HttpOnly; SameSite=lax
```

### 3. Network Tab - Request Headers

1. In the same Network request
2. Go to "Request Headers"
3. Look for `Cookie` header

**What you should see:**
```
Cookie: session=...; ext_name=...
```

**If you only see:**
```
Cookie: ext_name=...
```

Then the session cookie isn't being sent!

## Common Issues

### Issue 1: Domain Mismatch
**Symptom:** Cookie domain is `127.0.0.1` but you're accessing via `localhost`

**Fix:** Always use `localhost` (not `127.0.0.1`)

### Issue 2: Path Mismatch
**Symptom:** Cookie path is `/auth` but you're accessing `/`

**Fix:** Cookie path should be `/` (we set this in SessionMiddleware)

### Issue 3: SameSite Blocking
**Symptom:** Cookie exists but browser blocks it on redirect

**Fix:** `SameSite=lax` should work, but try accessing directly (no redirect)

### Issue 4: Cookie Not Being Set
**Symptom:** No `Set-Cookie` header in response

**Fix:** Check server logs for session middleware errors

## Quick Test

1. **Clear ALL cookies** for `localhost:8000`
2. **Visit:** `http://localhost:8000/auth/debug/session`
3. **Check Network tab** → Response Headers → `Set-Cookie`
4. **Check Application tab** → Cookies → `session` cookie
5. **Visit again:** `http://localhost:8000/auth/debug/session`
6. **Check Network tab** → Request Headers → `Cookie`

The session cookie should appear in BOTH:
- Response Headers (Set-Cookie) - when server sets it
- Request Headers (Cookie) - when browser sends it back

## Share This Info

Please share:
1. Cookie attributes from DevTools (Domain, Path, SameSite, HttpOnly)
2. Set-Cookie header from Network → Response Headers
3. Cookie header from Network → Request Headers (if present)

This will help identify why the cookie isn't being sent back!








