# IAM Policy Update Required

## Issue

The current IAM policy has a condition that's blocking `iam:CreateRole` permission. The policy needs to be updated to allow role creation.

## Quick Fix

Update your IAM policy `LLMDuelArenaDeploymentPolicy` in AWS:

1. **Go to IAM → Policies**
2. **Find and click** `LLMDuelArenaDeploymentPolicy`
3. **Click "Edit"**
4. **Replace the IAM section** with:

```json
{
  "Sid": "IAMLambdaRoles",
  "Effect": "Allow",
  "Action": [
    "iam:CreateRole",
    "iam:GetRole",
    "iam:UpdateRole",
    "iam:DeleteRole",
    "iam:AttachRolePolicy",
    "iam:DetachRolePolicy",
    "iam:ListRolePolicies",
    "iam:ListAttachedRolePolicies",
    "iam:PutRolePolicy",
    "iam:DeleteRolePolicy",
    "iam:GetRolePolicy"
  ],
  "Resource": [
    "arn:aws:iam::*:role/llm-duel-arena-*"
  ]
},
{
  "Sid": "IAMPassRole",
  "Effect": "Allow",
  "Action": [
    "iam:PassRole"
  ],
  "Resource": [
    "arn:aws:iam::*:role/llm-duel-arena-*"
  ],
  "Condition": {
    "StringEquals": {
      "iam:PassedToService": "lambda.amazonaws.com"
    }
  }
}
```

5. **Click "Save changes"**

## What Changed

- **Before**: All IAM actions had a condition that blocked `CreateRole`
- **After**: `CreateRole` and other role management actions work without conditions
- **Security**: `PassRole` still has the condition to only allow passing roles to Lambda

## Full Updated Policy

See `AWS_IAM_PERMISSIONS.md` for the complete updated policy.




