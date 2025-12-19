# Quick Fix: Invalid Scope Error

## The Problem
You're getting: `invalid_scope` error when trying to login with Cognito.

## The Solution (2 minutes)

### Step 1: Enable Scopes in Cognito (1 minute)

1. **Open AWS Console** → Go to **Cognito** service
2. Click on your **User Pool** (e.g., `eu-north-1_6WUbLC1KS`)
3. Click **"App integration"** tab (left sidebar)
4. Under **"App clients"**, click on your app client name
5. Scroll down to **"Hosted UI"** section
6. Find **"Allowed OAuth scopes"**
7. **Check these three boxes:**
   - ✅ **openid**
   - ✅ **email**  
   - ✅ **profile**
8. Click **"Save changes"** button at the bottom

### Step 2: Verify Other Settings (30 seconds)

While you're there, make sure:

- **Allowed OAuth flows**: ✅ **Authorization code grant** is checked
- **Allowed callback URLs**: Contains `http://localhost:8000/auth/callback`
- **Allowed sign-out URLs**: Contains `http://localhost:8000/`

### Step 3: Restart Application (30 seconds)

```bash
# Stop your server (Ctrl+C in terminal)
# Then restart:
uvicorn app.main:app --reload
```

### Step 4: Test Login

1. Go to `http://localhost:8000/`
2. Click **"Sign In with Cognito"**
3. Should redirect to Cognito login page (no error!)

## Visual Guide

In Cognito App Client settings, you should see:

```
┌─────────────────────────────────────────┐
│ Hosted UI                               │
├─────────────────────────────────────────┤
│ Allowed callback URLs:                  │
│   http://localhost:8000/auth/callback  │
│                                         │
│ Allowed sign-out URLs:                  │
│   http://localhost:8000/                │
│                                         │
│ Allowed OAuth flows:                   │
│   ☑ Authorization code grant           │
│                                         │
│ Allowed OAuth scopes:                  │
│   ☑ openid                             │ ← CHECK THIS
│   ☑ email                              │ ← CHECK THIS
│   ☑ profile                            │ ← CHECK THIS
│   ☐ aws.cognito.signin.user.admin      │
│   ☐ phone                              │
└─────────────────────────────────────────┘
```

## Alternative: Use Only Required Scopes

If you want to use fewer scopes, you can update your `.env`:

```bash
# Use only openid and email (minimal)
COGNITO_SCOPES=openid email
```

Then enable only `openid` and `email` in Cognito (not `profile`).

## Still Not Working?

1. **Double-check** the scopes are saved in Cognito
2. **Wait 30 seconds** after saving (Cognito can take a moment to propagate)
3. **Clear browser cache** and try again
4. **Check server logs** for any other errors

## Success Indicators

✅ No error when clicking "Sign In with Cognito"
✅ Redirects to Cognito login page
✅ Can sign in/sign up
✅ Redirects back to your app after login
✅ User info appears in top-right corner

