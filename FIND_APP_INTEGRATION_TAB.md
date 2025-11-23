# How to Find App Integration Tab in AWS Cognito

## Step-by-Step Navigation

### From the Overview Page (where you are now):

1. **Look at the left sidebar** - You'll see "Applications" (it's collapsed)
2. **Click on "Applications"** - It will expand
3. **Click on "App clients"** - This takes you to the App clients page
4. **Click on your App Client name** (e.g., "Ilm-arena" or the client ID)
5. **You'll see tabs at the top** - One of them is **"App integration"**

### Alternative Path:

1. From Overview page, click the **"Set up your app: Ilm-arena"** card
2. Click **"View quick setup guide"**
3. This will take you directly to the App Client configuration

### Visual Guide:

```
Left Sidebar Navigation:
├── Overview (you are here)
├── Applications ▼
│   └── App clients ← Click here
│       └── [Your App Client] ← Click on it
│           └── Tabs appear:
│               ├── App integration ← THIS IS WHAT YOU NEED!
│               ├── Hosted UI
│               └── Advanced app client settings
```

## What You'll See in App Integration Tab:

Once you're in the App integration tab, you'll see:

1. **App client information**
   - Client ID
   - Client secret (if enabled)

2. **Hosted UI section** (this is what you need!)
   - Allowed callback URLs
   - Allowed sign-out URLs
   - Allowed OAuth flows
   - **Allowed OAuth scopes** ← Enable scopes here!

3. **Advanced settings**

## Quick Access:

**Direct URL pattern:**
```
https://console.aws.amazon.com/cognito/v2/idp/user-pools/eu-north-1_6WUbLC1KS/app-integration
```

Replace `eu-north-1_6WUbLC1KS` with your User Pool ID if different.

## What to Do Once You're There:

1. Scroll down to **"Hosted UI"** section
2. Find **"Allowed OAuth scopes"**
3. Check these boxes:
   - ✅ **openid**
   - ✅ **email**
   - ✅ **profile**
4. Click **"Save changes"**

That's it! The invalid_scope error will be fixed.

