# Cognito HTTP Callback Requirement

## Important: Use `localhost`, Not `127.0.0.1`

AWS Cognito has a strict requirement for HTTP callback URLs:

> **"HTTPS is required over HTTP except for http://localhost"**

This means:
- ✅ `http://localhost:8000/auth/callback` - **ALLOWED** (HTTP is OK)
- ❌ `http://127.0.0.1:8000/auth/callback` - **REJECTED** (requires HTTPS)

## Solution

### 1. Update Your `.env` File

Make sure your callback URL uses `localhost`:

```bash
COGNITO_CALLBACK_URL=http://localhost:8000/auth/callback
COGNITO_LOGOUT_URL=http://localhost:8000/
```

### 2. Update Cognito App Client Settings

In AWS Console → Cognito → User Pool → App Client:

**Allowed callback URLs:**
```
http://localhost:8000/auth/callback
```

**Allowed sign-out URLs:**
```
http://localhost:8000/
```

### 3. Access Your App via `localhost`

Even if you access your app via `http://127.0.0.1:8000`, the callback URL **must** use `localhost`:

- ✅ Access app: `http://127.0.0.1:8000` (works fine)
- ✅ Callback URL: `http://localhost:8000/auth/callback` (required by Cognito)
- ✅ Browser cookies: Will work because both `localhost` and `127.0.0.1` cookies are accessible

The code now automatically converts `127.0.0.1` to `localhost` in the callback URL to meet Cognito's requirements.

## Why This Works

Modern browsers treat `localhost` and `127.0.0.1` as the same origin for cookie purposes in local development. So:
- Session cookie set for `127.0.0.1:8000` ✅
- Cognito redirects to `localhost:8000/auth/callback` ✅
- Browser sends the cookie ✅
- Session state is preserved ✅

## Testing

1. Update `.env` to use `localhost` in callback URLs
2. Update Cognito App Client settings
3. Restart your server
4. Access app via either `localhost:8000` or `127.0.0.1:8000`
5. Try login - it should work now!




