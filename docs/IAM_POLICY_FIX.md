# IAM Policy Fix - Critical Issue

## Problem

Your IAM policy currently has a condition (`iam:PassedToService = lambda.amazonaws.com`) applied to **ALL** IAM actions, including `CreateRole`. This condition only makes sense for `PassRole` and will block role creation.

## Current (Broken) Configuration

In AWS Console, IAM service shows:
- **Request condition:** `iam:PassedToService = lambda.amazonaws.com` ❌

This condition blocks `CreateRole`, `UpdateRole`, `DeleteRole`, etc.

## Required Fix

You need **TWO separate IAM statements**:

### Statement 1: Role Management (NO Condition)
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
}
```

### Statement 2: PassRole (WITH Condition)
```json
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

## How to Fix in AWS Console

### Option 1: Edit Policy JSON Directly

1. Go to **IAM → Policies → LLMDuelArenaDeploymentPolicy**
2. Click **"Edit"**
3. Click **"JSON"** tab
4. Find the IAM statement(s)
5. Replace with the two statements above
6. Click **"Next"** → **"Save changes"**

### Option 2: Use Visual Editor

1. Go to **IAM → Policies → LLMDuelArenaDeploymentPolicy**
2. Click **"Edit"**
3. Find the **IAM** service statement
4. **Remove the condition** from the main statement
5. **Add a new statement** for `PassRole` with the condition
6. Click **"Next"** → **"Save changes"**

## Verification

After updating, verify:
- ✅ IAM service should show **TWO statements** (or one without condition)
- ✅ `CreateRole` should work without conditions
- ✅ `PassRole` should have condition `iam:PassedToService = lambda.amazonaws.com`

## Complete Policy

See `AWS_IAM_PERMISSIONS.md` for the complete updated policy JSON that you can copy-paste.





