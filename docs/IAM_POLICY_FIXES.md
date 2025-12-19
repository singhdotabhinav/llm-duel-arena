# IAM Policy Fixes - December 2024

## Issues Found

### 1. ❌ API Gateway Tags Permission Missing

**Error:**
```
AccessDeniedException: User ... is not authorized to perform: apigateway:POST 
on resource: arn:aws:apigateway:*::/tags/arn:aws:apigateway:us-east-1::/v2/apis/*
```

**Root Cause:** API Gateway v2 resources use tags with complex resource ARNs that include the full resource ARN being tagged.

**Fix Applied:** ✅ Added separate `APIGatewayTags` statement with:
- `apigateway:POST`, `apigateway:GET`, `apigateway:DELETE` actions
- Resource patterns: `/tags/*` and `/tags/arn*` to match nested tag ARNs

### 2. ❌ IAM TagRole Permission Missing

**Error:**
```
AccessDenied: User ... is not authorized to perform: iam:TagRole
```

**Root Cause:** Terraform needs permission to tag IAM roles when creating them.

**Fix Applied:** ✅ Added to `IAMLambdaRoles` statement:
- `iam:TagRole`
- `iam:UntagRole`
- `iam:ListRoleTags`

### 3. ❌ IAM CreateRole Still Failing

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

Check you have **TWO API Gateway statements**:

1. **APIGatewayAll** statement:
```json
{
  "Sid": "APIGatewayAll",
  "Effect": "Allow",
  "Action": ["apigateway:*"],
  "Resource": [
    "arn:aws:apigateway:*::/apis/*",
    "arn:aws:apigateway:*::/apis/*/*",
    "arn:aws:apigateway:*::/restapis/*",
    "arn:aws:apigateway:*::/restapis/*/*"
  ]
}
```

2. **APIGatewayTags** statement (NEW):
```json
{
  "Sid": "APIGatewayTags",
  "Effect": "Allow",
  "Action": ["apigateway:POST", "apigateway:GET", "apigateway:DELETE"],
  "Resource": [
    "arn:aws:apigateway:*::/tags/*",
    "arn:aws:apigateway:*::/tags/arn*"
  ]
}
```

### Step 4: Verify IAM Tagging Permissions

Check the `IAMLambdaRoles` statement includes:
```json
"Action": [
  "iam:CreateRole",
  "iam:TagRole",      // ← Must include this!
  "iam:UntagRole",    // ← Must include this!
  "iam:ListRoleTags", // ← Must include this!
  // ... other role actions
]
```

### Step 5: Test Terraform

```bash
cd infrastructure/environments/int
terraform plan
```

Expected: ✅ No `AccessDenied` errors for:
- `iam:CreateRole`
- `iam:TagRole`
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

