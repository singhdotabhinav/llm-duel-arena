# AWS Cognito Setup Guide - From Scratch

This guide will walk you through setting up AWS Cognito from scratch for local testing.

## Prerequisites

- AWS Account (free tier is fine)
- AWS Console access
- About 10-15 minutes

## Step 1: Navigate to Cognito

1. Log in to [AWS Console](https://console.aws.amazon.com/)
2. Search for "Cognito" in the top search bar
3. Click on **"Amazon Cognito"**
4. Click **"Create user pool"** (or "User pools" → "Create user pool")

## Step 2: Configure Sign-In Options

1. **Sign-in options**: Select **"Email"** ✅
   - Uncheck "Phone number" if checked
   - Uncheck "Username" if checked
   - Keep only "Email" selected

2. Click **"Next"**

## Step 3: Configure Security Requirements

1. **Password policy**: 
   - Choose **"Cognito defaults"** (recommended for testing)
   - Or customize if you prefer

2. **Multi-factor authentication (MFA)**:
   - Select **"No MFA"** (for local testing)
   - You can enable MFA later for production

3. **User account recovery**:
   - Keep defaults (email verification)

4. Click **"Next"**

## Step 4: Configure Sign-Up Experience

1. **Self-service sign-up**:
   - Select **"Enable self-service sign-up"** ✅
   - This allows users to create accounts

2. **Cognito-assisted verification**:
   - Select **"Send email with Cognito"** ✅
   - This uses Cognito's built-in email service (free tier: 50 emails/day)

3. **Required attributes**:
   - Keep **"email"** selected ✅
   - You can add more if needed (name, etc.)

4. Click **"Next"**

## Step 5: Configure Message Delivery

1. **Email provider**:
   - Select **"Send email with Cognito"** ✅
   - This is free and sufficient for testing
   - For production, you can configure SES later

2. Click **"Next"**

## Step 6: Integrate Your App

1. **User pool name**: 
   - Enter: `llm-duel-arena-local` (or any name you prefer)

2. **App client**:
   - Click **"Add an app client"**
   - **App client name**: `local-test-client`
   - **Client secret**: 
     - ⚠️ **IMPORTANT**: Uncheck **"Generate client secret"**
     - This creates a public client (required for web apps)
   - Click **"Next"**

3. **App client settings**:
   - **Authentication flows**:
     - ✅ Check **"ALLOW_USER_PASSWORD_AUTH"** (for programmatic login)
     - ✅ Check **"ALLOW_REFRESH_TOKEN_AUTH"** (for token refresh)
   - **Advanced app client settings**:
     - Leave defaults
   - Click **"Next"**

4. Click **"Next"** to continue

## Step 7: Configure App Client OAuth Settings

1. **Hosted UI**:
   - ✅ Check **"Use the Cognito Hosted UI"**

2. **Allowed callback URLs**:
   - Add: `http://localhost:8000/auth/callback`
   - Click **"Add callback URL"** after entering

3. **Allowed sign-out URLs**:
   - Add: `http://localhost:8000/`
   - Click **"Add sign-out URL"** after entering

4. **OAuth 2.0 grant types**:
   - ✅ Check **"Authorization code grant"**
   - ✅ Check **"Implicit grant"** (optional, but recommended)

5. **OpenID Connect scopes**:
   - ✅ Check **"openid"**
   - ✅ Check **"email"**
   - ✅ Check **"profile"**

6. Click **"Next"**

## Step 8: Review and Create

1. **Review** all your settings:
   - User pool name: `llm-duel-arena-local`
   - Sign-in: Email
   - MFA: No MFA
   - Self-service sign-up: Enabled
   - App client: `local-test-client` (no secret)
   - Callback URL: `http://localhost:8000/auth/callback`
   - Sign-out URL: `http://localhost:8000/`

2. Click **"Create user pool"**

3. Wait for creation (usually 10-30 seconds)

## Step 9: Get Your Cognito Details

After creation, you'll see a success message. Now you need to collect the following information:

### Option A: From the Success Page

1. You should see a page with your user pool details
2. Note down:
   - **User Pool ID**: `us-east-1_XXXXXXXXX` (format: `region_XXXXXXXXX`)
   - **App Client ID**: A long alphanumeric string

### Option B: From User Pool Details

1. Click on your user pool name (`llm-duel-arena-local`)
2. On the **"General settings"** tab, find:
   - **User Pool ID**: Copy this
3. Go to **"App integration"** tab → **"App clients"**
4. Click on your app client (`local-test-client`)
5. Find **"Client ID"**: Copy this

### Option C: Get Cognito Domain

1. Go to **"App integration"** tab
2. Scroll to **"Domain"** section
3. If no domain exists:
   - Click **"Create Cognito domain"**
   - Enter a unique prefix (e.g., `llm-duel-arena-local`)
   - Click **"Create Cognito domain"**
   - Wait a few seconds
4. Copy the **domain** (e.g., `llm-duel-arena-local.auth.us-east-1.amazoncognito.com`)

## Step 10: Update Your .env File

Now update your `.env` file with the Cognito details:

```bash
# AWS Cognito
USE_COGNITO=true
COGNITO_USER_POOL_ID=us-east-1_XXXXXXXXX  # From Step 9
COGNITO_CLIENT_ID=your-app-client-id      # From Step 9
COGNITO_CLIENT_SECRET=                     # Leave empty (no secret)
COGNITO_REGION=us-east-1                   # Your region (from User Pool ID)
COGNITO_DOMAIN=llm-duel-arena-local.auth.us-east-1.amazoncognito.com  # From Step 9
COGNITO_CALLBACK_URL=http://localhost:8000/auth/callback
COGNITO_LOGOUT_URL=http://localhost:8000/
COGNITO_SCOPES=openid email profile
```

## Step 11: Create a Test User (Optional)

You can create a test user to test login:

1. Go to your User Pool → **"Users"** tab
2. Click **"Create user"**
3. **Username**: Leave empty (will use email)
4. **Email address**: Enter your email (e.g., `test@example.com`)
5. **Temporary password**: Enter a password (you'll change it on first login)
6. ✅ Check **"Send an email invitation"** (optional)
7. Click **"Create user"**

## Step 12: Test Your Setup

1. **Start your application**:
   ```bash
   uvicorn app.main:app --reload
   ```

2. **Open browser**: http://localhost:8000

3. **Test sign-up**:
   - Click "Sign Up"
   - You should be redirected to Cognito Hosted UI
   - Create a new account
   - Verify email (check your inbox)
   - You'll be redirected back to `http://localhost:8000/auth/callback`

4. **Test login**:
   - Click "Login"
   - Enter your credentials
   - You should be logged in

## Troubleshooting

### Issue: "Invalid redirect URI"

**Solution**: 
- Go to Cognito → Your User Pool → App integration → App clients → Your client
- Make sure `http://localhost:8000/auth/callback` is in "Allowed callback URLs"
- Make sure you're using `localhost` (not `127.0.0.1`)

### Issue: "App client has a client secret"

**Solution**:
- You need a public client (no secret) for web apps
- Delete the app client and create a new one with "Generate client secret" **unchecked**

### Issue: "Cognito domain not found"

**Solution**:
- Go to App integration → Domain
- Create a Cognito domain if you haven't
- Use the domain in your `.env` file

### Issue: "Email verification not working"

**Solution**:
- Check your email spam folder
- Cognito free tier allows 50 emails/day
- For testing, you can manually verify users in Cognito Console → Users → Select user → "Confirm user"

## Quick Reference

### Cognito URLs You'll Need

- **User Pool ID**: `us-east-1_XXXXXXXXX`
- **App Client ID**: `xxxxxxxxxxxxxxxxxxxx`
- **Cognito Domain**: `your-prefix.auth.us-east-1.amazoncognito.com`
- **Region**: `us-east-1` (or your chosen region)

### Important Settings Summary

- ✅ Email sign-in enabled
- ✅ Self-service sign-up enabled
- ✅ Public app client (no secret)
- ✅ Callback URL: `http://localhost:8000/auth/callback`
- ✅ Sign-out URL: `http://localhost:8000/`
- ✅ OAuth scopes: `openid email profile`
- ✅ Authorization code grant enabled

## Next Steps

Once Cognito is set up:

1. ✅ Update `.env` with your Cognito details
2. ✅ Set up DynamoDB tables (see LOCAL_TESTING_GUIDE.md)
3. ✅ Install Ollama and pull models
4. ✅ Run the application locally
5. ✅ Test authentication flow

## Cost

- **Cognito Free Tier**: 
  - 50,000 Monthly Active Users (MAU)
  - 50 emails/day via Cognito email service
  - Perfect for local testing and development!

You should stay well within free tier limits for local development.

