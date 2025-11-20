# OAuth CSRF State Mismatch - Troubleshooting

## Error
```
mismatching_state: CSRF Warning! State not equal in request and response
```

## Quick Fixes

### 1. Clear Browser Cookies
The most common fix - clear localhost cookies or use incognito mode.

### 2. Verify Google Cloud Console
- Go to: https://console.cloud.google.com/apis/credentials
- Check "Authorized redirect URIs" has EXACTLY: `http://localhost:8000/auth/callback`
- No trailing slash, no https, use "localhost" not "127.0.0.1"

### 3. Check OAuth Consent Screen
If your app is in "Testing" mode, add your email to "Test users"

### 4. Restart Server
```bash
# Stop server (Ctrl+C)
uvicorn app.main:app --reload
```

## If Still Not Working

Try accessing with the exact domain in your redirect URI:
- Use `http://localhost:8000` (not `http://127.0.0.1:8000`)
- Check browser URL matches redirect URI domain

## Alternative: Use 127.0.0.1

If localhost doesn't work, try using 127.0.0.1 instead:

1. Update `.env`:
   ```bash
   GOOGLE_REDIRECT_URI=http://127.0.0.1:8000/auth/callback
   ```

2. Update Google Cloud Console redirect URI to: `http://127.0.0.1:8000/auth/callback`

3. Restart server

4. Access app at: `http://127.0.0.1:8000`









