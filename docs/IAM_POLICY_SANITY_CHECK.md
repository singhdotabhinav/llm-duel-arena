# IAM Policy Sanity Check

## ✅ Policy Structure Verification

The policy in `AWS_IAM_PERMISSIONS.md` is **correctly structured**. Here's what to verify:

### Critical Check: IAM Statements Must Be Separate

The policy has **TWO separate IAM statements**:

1. **Statement 1: IAMLambdaRoles** (Sid: "IAMLambdaRoles")
   ```json
   {
     "Sid": "IAMLambdaRoles",
     "Effect": "Allow",
     "Action": [
       "iam:CreateRole",      // ← NO CONDITION - This is critical!
       "iam:GetRole",
       "iam:UpdateRole",
       "iam:DeleteRole",
       // ... other role management actions
     ],
     "Resource": ["arn:aws:iam::*:role/llm-duel-arena-*"]
     // NO Condition block here!
   }
   ```

2. **Statement 2: IAMPassRole** (Sid: "IAMPassRole")
   ```json
   {
     "Sid": "IAMPassRole",
     "Effect": "Allow",
     "Action": ["iam:PassRole"],
     "Resource": ["arn:aws:iam::*:role/llm-duel-arena-*"],
     "Condition": {                    // ← Condition ONLY here!
       "StringEquals": {
         "iam:PassedToService": "lambda.amazonaws.com"
       }
     }
   }
   ```

## 🔍 How to Verify in AWS Console

### Step 1: Check Policy JSON Structure

1. Go to **IAM → Users → llm-duel-arena-deploy**
2. Click on the policy name (either inline or managed policy)
3. Click **"JSON"** tab
4. Verify you see **TWO separate statements** for IAM:
   - One statement with `CreateRole` and **NO Condition**
   - One statement with `PassRole` and **WITH Condition**

### Step 2: Check Visual Summary (May Be Misleading)

⚠️ **Warning**: The visual summary table in AWS Console may show:
- "IAM" service with condition `iam:PassedToService = lambda.amazonaws.com`

This is **misleading** - it's showing the condition because one statement has it, but it should NOT apply to `CreateRole`.

**To verify correctly:**
1. Click on the **IAM** row in the summary table
2. Expand to see individual actions
3. Verify:
   - `CreateRole` shows **NO condition** ✅
   - `PassRole` shows condition `iam:PassedToService = lambda.amazonaws.com` ✅

### Step 3: Test with Terraform

The real test is whether Terraform can create roles:

```bash
cd infrastructure/environments/int
terraform plan
```

If you see errors like:
- ❌ `AccessDenied: User ... is not authorized to perform: iam:CreateRole`

Then the condition is incorrectly applied to `CreateRole`.

## 🐛 Common Mistakes

### ❌ Wrong: Single Statement with Condition

```json
{
  "Sid": "IAMAll",
  "Effect": "Allow",
  "Action": [
    "iam:CreateRole",  // ← This will FAIL!
    "iam:PassRole"
  ],
  "Resource": ["arn:aws:iam::*:role/llm-duel-arena-*"],
  "Condition": {  // ← Condition blocks CreateRole!
    "StringEquals": {
      "iam:PassedToService": "lambda.amazonaws.com"
    }
  }
}
```

### ✅ Correct: Two Separate Statements

```json
[
  {
    "Sid": "IAMLambdaRoles",
    "Effect": "Allow",
    "Action": ["iam:CreateRole", "iam:GetRole", ...],
    "Resource": ["arn:aws:iam::*:role/llm-duel-arena-*"]
    // NO Condition
  },
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
]
```

## 📋 Quick Verification Checklist

- [ ] Policy has **TWO separate IAM statements**
- [ ] `CreateRole` is in a statement **WITHOUT** a Condition block
- [ ] `PassRole` is in a statement **WITH** a Condition block
- [ ] Both statements have the same Resource ARN pattern
- [ ] Policy JSON is valid (no syntax errors)
- [ ] Policy is attached to user `llm-duel-arena-deploy`
- [ ] Terraform `plan` command runs without IAM errors

## 🧪 Test Command

Run this to verify Terraform can create roles:

```bash
cd /Users/abhinav/projects/llm-duel-arena/infrastructure/environments/int
terraform init
terraform plan
```

Expected output:
- ✅ No `AccessDenied` errors for `iam:CreateRole`
- ✅ Terraform shows it will create `aws_iam_role.lambda_role`

If you see `AccessDenied` for `CreateRole`, the policy needs to be fixed.

