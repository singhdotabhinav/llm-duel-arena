# Fix Cognito OAuth Scope Error

## Error Message

```
Invalid scope error: invalid_scope. Requested scopes: 'openid email profile'
```

## What This Means

Your Cognito App Client doesn't have the required OAuth scopes enabled. The application needs these scopes to authenticate users and get their email/profile information.

## Quick Fix (3 Minutes)

### Step 1: Open Cognito Console

1. Go to: https://console.aws.amazon.com/cognito/
2. Click **"User pools"**
3. Click your user pool: **`us-east-1_7fscSPSUe`**

### Step 2: Navigate to App Client

1. Click **"App integration"** tab
2. Scroll to **"App clients"** section
3. Click on your app client: **`2v96lg57eesiuln067hh5mgol9`**

### Step 3: Enable OAuth Scopes

1. Scroll down to **"Hosted UI"** section
2. Find **"Allowed OAuth scopes"**
3. Click **"Edit"**
4. You'll see a list of available scopes. **Check these three**:
   - ✅ **openid** (OpenID Connect)
   - ✅ **email** (Email address)
   - ✅ **profile** (User profile)
5. Click **"Save changes"**

### Step 4: Verify OAuth Flows

While you're in the same section, make sure:
- ✅ **Authorization code grant** is enabled
- ✅ **Implicit grant** is enabled (optional but recommended)

### Step 5: Verify Callback URLs

Also check that these are set:

**Allowed callback URLs:**
```
http://localhost:8000/auth/callback
```

**Allowed sign-out URLs:**
```
http://localhost:8000/
```

## Complete Configuration Checklist

Your Cognito App Client should have:

### OAuth 2.0 Grant Types
- ✅ Authorization code grant
- ✅ Implicit grant (optional)

### Allowed OAuth Scopes
- ✅ openid
- ✅ email
- ✅ profile

### Callback URLs
- ✅ `http://localhost:8000/auth/callback`

### Sign-Out URLs
- ✅ `http://localhost:8000/`

## After Fixing

1. **Save all changes** in Cognito
2. **Restart your local server** (if running):
   ```bash
   # Press Ctrl+C to stop
   # Then restart:
   uvicorn app.main:app --reload
   ```
3. **Try logging in again** at http://localhost:8000
4. You should now be redirected to Cognito Hosted UI successfully!

## Visual Guide

The "Allowed OAuth scopes" section should look like this:

```
Allowed OAuth scopes
[Edit]

☑ openid
☑ email  
☑ profile
☐ phone
☐ aws.cognito.signin.user.admin
☐ address
```

Make sure the first three are checked!

## Troubleshooting

### Still Getting "invalid_scope" Error?

1. **Double-check** that all three scopes are enabled:
   - openid ✅
   - email ✅
   - profile ✅

2. **Verify** your `.env` file has:
   ```bash
   COGNITO_SCOPES=openid email profile
   ```

3. **Clear browser cache** and try again

4. **Restart your server** after making Cognito changes

### Error: "redirect_uri_mismatch"

This is a different error. See `docs/COGNITO_CALLBACK_FIX.md` for help.

## Quick Test

After enabling scopes, test the login URL directly:

```
https://us-east-17fscspsue.auth.us-east-1.amazoncognito.com/login?client_id=2v96lg57eesiuln067hh5mgol9&response_type=code&redirect_uri=http://localhost:8000/auth/callback&scope=openid+email+profile
```

If this works without errors, the scopes are configured correctly!

