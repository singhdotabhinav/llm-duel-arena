# IAM Policy Fixes - December 2024

## Issues Found

### 1. ❌ API Gateway Tags Permission Missing

**Error:**
```
AccessDeniedException: User ... is not authorized to perform: apigateway:POST 
on resource: arn:aws:apigateway:*::/tags/*
```

**Root Cause:** API Gateway v2 resources use tags, and the resource ARN pattern didn't include `/tags/*`.

**Fix Applied:** ✅ Updated `APIGatewayAll` statement to include:
- `arn:aws:apigateway:*::/tags/*`
- `arn:aws:apigateway:*::/apis/*/*` (for nested resources)
- `arn:aws:apigateway:*::/restapis/*/*` (for REST API nested resources)

### 2. ❌ IAM CreateRole Still Failing

**Error:**
```
AccessDenied: User ... is not authorized to perform: iam:CreateRole
```

**Root Cause:** The policy structure is correct in the document, but may not be applied correctly in AWS.

**Possible Issues:**
1. Policy wasn't updated in AWS console
2. Old policy version still active
3. Condition incorrectly applied to CreateRole statement

## Action Required

### Step 1: Update Policy in AWS Console

1. Go to **IAM → Users → llm-duel-arena-deploy**
2. Click on your policy (inline or managed)
3. Click **"Edit"** → **"JSON"** tab
4. **Copy the ENTIRE policy JSON** from `docs/AWS_IAM_PERMISSIONS.md` (lines 41-123)
5. **Replace** the existing JSON
6. Click **"Next"** → **"Save changes"**

### Step 2: Verify Policy Structure

After updating, verify in the JSON tab:

✅ **Must have TWO separate IAM statements:**

1. **IAMLambdaRoles** statement:
   ```json
   {
     "Sid": "IAMLambdaRoles",
     "Effect": "Allow",
     "Action": ["iam:CreateRole", "iam:GetRole", ...],
     "Resource": ["arn:aws:iam::*:role/llm-duel-arena-*"]
     // NO "Condition" block here!
   }
   ```

2. **IAMPassRole** statement:
   ```json
   {
     "Sid": "IAMPassRole",
     "Effect": "Allow",
     "Action": ["iam:PassRole"],
     "Resource": ["arn:aws:iam::*:role/llm-duel-arena-*"],
     "Condition": {
       "StringEquals": {
         "iam:PassedToService": "lambda.amazonaws.com"
       }
     }
   }
   ```

### Step 3: Verify API Gateway Resources

Check the `APIGatewayAll` statement includes:
```json
"Resource": [
  "arn:aws:apigateway:*::/apis/*",
  "arn:aws:apigateway:*::/apis/*/*",
  "arn:aws:apigateway:*::/tags/*",        // ← Must include this!
  "arn:aws:apigateway:*::/restapis/*",
  "arn:aws:apigateway:*::/restapis/*/*"
]
```

### Step 4: Test Terraform

```bash
cd infrastructure/environments/int
terraform plan
```

Expected: ✅ No `AccessDenied` errors for:
- `iam:CreateRole`
- `apigateway:POST` on `/tags/*`

## Quick Verification Script

Run this to verify your local policy document:

```bash
cd /Users/abhinav/projects/llm-duel-arena
python3 scripts/verify_iam_policy.py
```

Should output:
```
✅ POLICY STRUCTURE IS CORRECT!
```

## Summary

- ✅ Policy document updated with API Gateway tags permission
- ✅ Policy structure verified (CreateRole and PassRole are separate)
- ⚠️ **Action Required:** Update policy in AWS Console with latest JSON

