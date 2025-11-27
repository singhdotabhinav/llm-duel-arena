# Fix: Domain Mismatch Issue

## Problem

Your app is accessed via `http://127.0.0.1:8000` but your Cognito callback URL is configured as `http://localhost:8000/auth/callback`.

**Browsers treat `localhost` and `127.0.0.1` as different domains!** This means:
- Session cookie is set for `127.0.0.1:8000`
- Cognito redirects to `localhost:8000/auth/callback`
- Browser doesn't send the cookie (different domain)
- Session state is lost → `mismatching_state` error

## Solution

You have two options:

### Option 1: Use `localhost` everywhere (Recommended)

1. **Access your app via `localhost`:**
   ```
   http://localhost:8000
   ```
   (Instead of `http://127.0.0.1:8000`)

2. **Keep your `.env` callback URL as:**
   ```bash
   COGNITO_CALLBACK_URL=http://localhost:8000/auth/callback
   ```

3. **Update Cognito App Client callback URL** to use `localhost`:
   - AWS Console → Cognito → User Pool → App Client
   - Under "Hosted UI" → "Allowed callback URLs"
   - Ensure it includes: `http://localhost:8000/auth/callback`

### Option 2: Use `127.0.0.1` everywhere

1. **Update your `.env` file:**
   ```bash
   COGNITO_CALLBACK_URL=http://127.0.0.1:8000/auth/callback
   COGNITO_LOGOUT_URL=http://127.0.0.1:8000/
   ```

2. **Update Cognito App Client callback URL** to use `127.0.0.1`:
   - AWS Console → Cognito → User Pool → App Client
   - Under "Hosted UI" → "Allowed callback URLs"
   - Change to: `http://127.0.0.1:8000/auth/callback`

3. **Restart your server**

## Quick Fix

**Easiest solution:** Just access your app via `localhost` instead of `127.0.0.1`:

```
http://localhost:8000
```

Then clear cookies and try login again!

