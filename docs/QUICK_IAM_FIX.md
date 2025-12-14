# 🚨 QUICK FIX: Update IAM Policy in AWS Console

## The Problem
Terraform is failing because the IAM policy in AWS doesn't have permission for `apigateway:POST` on `/apis`.

## The Solution (2 Minutes)

### Step 1: Copy the Policy JSON
1. Open `docs/AWS_IAM_PERMISSIONS.md`
2. Find the JSON block starting at line 41 (starts with `{`)
3. Copy **EVERYTHING** from line 41 to line 145 (the closing `}`)

### Step 2: Update in AWS Console
1. Go to: https://console.aws.amazon.com/iam/home#/users
2. Click on user: **llm-duel-arena-deploy**
3. Click **"Permissions"** tab
4. Find your policy (inline or managed) → Click **"Edit"**
5. Click **"JSON"** tab
6. **DELETE** all existing JSON
7. **PASTE** the copied JSON from Step 1
8. Click **"Next"** → **"Save changes"**

### Step 3: Verify
The policy should now include:
- ✅ `"arn:aws:apigateway:*::/apis"` in the Resource list
- ✅ `"arn:aws:apigateway:*::/*"` (wildcard) for maximum compatibility

### Step 4: Re-run CI/CD
Push a commit or re-run the workflow. It should work now.

---

## Why This Keeps Happening

The policy document in the repo is correct, but **AWS doesn't automatically sync**. You must manually update the policy in AWS Console each time we fix it.

## Prevention

After updating, verify the policy JSON in AWS matches the one in `docs/AWS_IAM_PERMISSIONS.md`.

