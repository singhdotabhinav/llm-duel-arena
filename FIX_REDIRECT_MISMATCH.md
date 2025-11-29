# Fix: redirect_mismatch Error

## Error Message

Cognito is showing: `error=redirect_mismatch`

This means **the callback URL in your authorization request doesn't match what's configured in Cognito App Client**.

## Solution

### Step 1: Check What Your App is Sending

Look at your server logs when you click "Sign In". You should see:

```
[Cognito OIDC] ===== REDIRECT URI DEBUG =====
[Cognito OIDC] Final redirect_uri being sent to Cognito: http://localhost:8000/auth/callback
[Cognito OIDC] ⚠️  Make sure this EXACT URL is in Cognito App Client → Allowed callback URLs:
[Cognito OIDC] ⚠️  http://localhost:8000/auth/callback
```

**Copy this exact URL** - this is what your app is sending to Cognito.

### Step 2: Update Cognito App Client Settings

Go to AWS Console → Cognito → User Pool → App Client:

1. Click on your App Client (client ID: `371gt7emopsic4tqut8o5s4qep`)
2. Scroll to **"Hosted UI"** section
3. Find **"Allowed callback URLs"**
4. **Replace** whatever is there with the EXACT URL from Step 1:
   ```
   http://localhost:8000/auth/callback
   ```
5. **Important:** 
   - Must be EXACT match (no trailing slash, no extra spaces)
   - Must use `localhost` (not `127.0.0.1`)
   - Case-sensitive
6. Click **"Save changes"**

### Step 3: Verify Your `.env` File

Make sure your `.env` has:

```bash
COGNITO_CALLBACK_URL=http://localhost:8000/auth/callback
```

**Important:** 
- Must use `localhost` (not `127.0.0.1`)
- No trailing slash
- Exact match

### Step 4: Restart and Test

1. **Restart your server**
2. **Clear browser cookies** for `localhost:8000`
3. **Try login again**

## Common Mistakes

### ❌ Wrong:
```
http://127.0.0.1:8000/auth/callback
http://localhost:8000/auth/callback/
http://localhost:8000/auth/callback (with trailing space)
```

### ✅ Correct:
```
http://localhost:8000/auth/callback
```

## Verification Checklist

- [ ] Server logs show: `Final redirect_uri being sent to Cognito: http://localhost:8000/auth/callback`
- [ ] Cognito App Client → Allowed callback URLs contains: `http://localhost:8000/auth/callback`
- [ ] `.env` file has: `COGNITO_CALLBACK_URL=http://localhost:8000/auth/callback`
- [ ] No trailing slashes or extra spaces
- [ ] Using `localhost` (not `127.0.0.1`)
- [ ] Server restarted after changes
- [ ] Browser cookies cleared

## Still Not Working?

If you still get `redirect_mismatch`:

1. **Check server logs** - copy the exact URL from the logs
2. **Check Cognito settings** - copy the exact URL from Cognito
3. **Compare character by character** - they must be identical
4. **Check for hidden characters** - spaces, tabs, etc.

Share:
- The exact URL from server logs
- The exact URL from Cognito settings
- Screenshot of Cognito App Client → Hosted UI section





