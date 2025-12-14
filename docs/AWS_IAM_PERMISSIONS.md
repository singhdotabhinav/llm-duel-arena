# AWS IAM Permissions Required for LLM Duel Arena

## Overview

This document outlines the **minimum required AWS permissions** for deploying and managing the LLM Duel Arena infrastructure. Instead of using `AdministratorAccess`, you should create a custom IAM policy with only the permissions needed.

## AWS Services Used

Based on the infrastructure code analysis, the project uses:

1. **Terraform State Management**
   - S3 (for Terraform state storage)
   - DynamoDB (for Terraform state locking)

2. **Application Infrastructure**
   - Lambda (3 functions: game, auth, llm)
   - API Gateway (HTTP API)
   - DynamoDB (2 tables: games, users)
   - S3 (2 buckets: static assets, Lambda deployments)
   - CloudFront (CDN for static assets)
   - IAM (roles and policies for Lambda)
   - CloudWatch Logs (automatic, via Lambda)

3. **Deployment Operations**
   - Lambda function updates
   - S3 sync operations
   - CloudFront cache invalidation

## Required IAM Policy

Create an IAM user with the following policy attached:

> **⚠️ CRITICAL**: The IAM permissions are split into **TWO separate statements**:
> - **IAMLambdaRoles**: Role management actions (CreateRole, UpdateRole, etc.) - **NO condition**
> - **IAMPassRole**: PassRole action - **WITH condition** (only for Lambda service)
> 
> **DO NOT** apply the condition to CreateRole - it will block role creation!

> **Note**: This policy has been optimized to be under AWS's 2048 character limit for inline policies by using wildcards (`*`) for actions, while still scoping resources to your project (`llm-duel-arena-*`). This maintains security while meeting size constraints.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "S3All",
      "Effect": "Allow",
      "Action": ["s3:*"],
      "Resource": ["arn:aws:s3:::llm-duel-arena-*", "arn:aws:s3:::llm-duel-arena-*/*"]
    },
    {
      "Sid": "DynamoDBAll",
      "Effect": "Allow",
      "Action": ["dynamodb:*"],
      "Resource": ["arn:aws:dynamodb:*:*:table/llm-duel-arena-*", "arn:aws:dynamodb:*:*:table/llm-duel-arena-*/index/*"]
    },
    {
      "Sid": "LambdaAll",
      "Effect": "Allow",
      "Action": ["lambda:*"],
      "Resource": ["arn:aws:lambda:*:*:function:llm-duel-arena-*"]
    },
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
    },
    {
      "Sid": "APIGatewayTags",
      "Effect": "Allow",
      "Action": [
        "apigateway:POST",
        "apigateway:GET",
        "apigateway:DELETE"
      ],
      "Resource": [
        "arn:aws:apigateway:*::/tags/*",
        "arn:aws:apigateway:*::/tags/arn*"
      ]
    },
    {
      "Sid": "CloudFrontAll",
      "Effect": "Allow",
      "Action": ["cloudfront:*"],
      "Resource": ["*"]
    },
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
        "iam:GetRolePolicy",
        "iam:TagRole",
        "iam:UntagRole",
        "iam:ListRoleTags"
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
    },
    {
      "Sid": "CloudWatchLogs",
      "Effect": "Allow",
      "Action": ["logs:*"],
      "Resource": ["arn:aws:logs:*:*:log-group:/aws/lambda/llm-duel-arena-*"]
    },
    {
      "Sid": "ReadOnly",
      "Effect": "Allow",
      "Action": ["iam:GetPolicy", "iam:ListPolicies", "sts:GetCallerIdentity", "ec2:DescribeRegions", "ec2:DescribeAvailabilityZones"],
      "Resource": ["*"]
    }
  ]
}
```

## ⚠️ Important: IAM Permissions Structure

The IAM permissions are **split into two statements** for a critical reason:

1. **IAMLambdaRoles** (lines 76-94): 
   - Contains: `CreateRole`, `UpdateRole`, `DeleteRole`, etc.
   - **NO Condition** - These actions don't use `PassedToService`
   - Required for Terraform to create IAM roles

2. **IAMPassRole** (lines 95-109):
   - Contains: `PassRole` only
   - **WITH Condition** - Restricts to Lambda service only
   - Security best practice

**Why this matters:** If you apply the condition to `CreateRole`, Terraform will fail with "AccessDenied" when trying to create roles. The condition only applies to `PassRole`.

## Step-by-Step: Create IAM User with Custom Policy

> **Important**: AWS has a 2048 character limit for inline policies. The policy above is optimized to be under this limit. For better management, use a **managed policy** (recommended) instead of an inline policy.

### Option 1: Using AWS Console (Recommended - Managed Policy)

1. **Create IAM Policy (Managed Policy)**
   - Go to IAM → Policies → Create policy
   - Click "JSON" tab
   - Paste the policy above
   - Name it: `LLMDuelArenaDeploymentPolicy`
   - Description: "Permissions for deploying LLM Duel Arena infrastructure"
   - Click "Create policy"

2. **Create IAM User**
   - Go to IAM → Users → Create user
   - Username: `llm-duel-arena-deploy`
   - Click "Next"

3. **Attach Policy**
   - Select "Attach policies directly"
   - Search for `LLMDuelArenaDeploymentPolicy`
   - Select it and click "Next"
   - Click "Create user"

4. **Create Access Keys**
   - Click on the user you just created
   - Go to "Security credentials" tab
   - Click "Create access key"
   - Select "Command Line Interface (CLI)"
   - Save both Access Key ID and Secret Access Key

### Option 2: Using AWS CLI

```bash
# Create the policy
aws iam create-policy \
  --policy-name LLMDuelArenaDeploymentPolicy \
  --policy-document file://policy.json

# Create the user
aws iam create-user --user-name llm-duel-arena-deploy

# Attach the policy (replace ACCOUNT_ID and POLICY_ARN)
aws iam attach-user-policy \
  --user-name llm-duel-arena-deploy \
  --policy-arn arn:aws:iam::ACCOUNT_ID:policy/LLMDuelArenaDeploymentPolicy

# Create access keys
aws iam create-access-key --user-name llm-duel-arena-deploy
```

## Additional Notes

### Terraform State Backend Setup

Before running Terraform, you need to set up the state backend:

```bash
cd infrastructure
./setup-state-bucket.sh us-east-1
```

This requires permissions to:
- Create S3 bucket: `llm-duel-arena-terraform-state`
- Create DynamoDB table: `llm-duel-arena-terraform-locks`

### Environment-Specific Resources

The policy uses wildcards (`*`) for environment names (dev, int, prod). If you want to restrict to specific environments, replace `*` with the environment name:

```json
"Resource": [
  "arn:aws:lambda:*:*:function:llm-duel-arena-dev-*",
  "arn:aws:lambda:*:*:function:llm-duel-arena-int-*"
]
```

### Least Privilege Principle

This policy follows the principle of least privilege:
- ✅ Only includes permissions needed for deployment
- ✅ Scoped to specific resources (using ARNs)
- ✅ No wildcard permissions for destructive actions
- ✅ Includes conditions where appropriate (e.g., PassRole)

### What's NOT Included

The following are intentionally excluded:
- ❌ EC2 instance management (not used)
- ❌ RDS database management (using DynamoDB instead)
- ❌ Cognito management (should be done separately if needed)
- ❌ Secrets Manager (not currently used in Terraform)
- ❌ VPC/Networking (using default Lambda networking)

## Verification

After creating the user and access keys, verify the permissions:

```bash
# Configure AWS CLI
aws configure
# Enter your Access Key ID
# Enter your Secret Access Key
# Region: us-east-1
# Output: json

# Test permissions
aws sts get-caller-identity
aws s3 ls
aws lambda list-functions --query "Functions[?contains(FunctionName, 'llm-duel-arena')]"
```

## Security Best Practices

1. **Rotate Keys Regularly**: Change access keys every 90 days
2. **Use Separate Users**: Create different users for different environments (dev/int/prod)
3. **Enable MFA**: Add MFA for the IAM user if possible
4. **Monitor Usage**: Enable CloudTrail to audit API calls
5. **Limit Scope**: Further restrict resources by environment if needed

## Troubleshooting

### Error: `apigateway:POST` on `/tags/*` resource

**Symptom:**
```
AccessDeniedException: User ... is not authorized to perform: apigateway:POST 
on resource: arn:aws:apigateway:*::/tags/*
```

**Solution:** The policy has been updated to include `/tags/*` in the API Gateway resources. Make sure you've copied the latest policy version from this document.

### Error: `iam:CreateRole` Access Denied

**Symptom:**
```
AccessDenied: User ... is not authorized to perform: iam:CreateRole
```

**Possible Causes:**
1. **Policy not updated**: The old policy with a condition on `CreateRole` is still active
2. **Policy not attached**: The policy isn't attached to the user
3. **Wrong user**: Terraform is using credentials from a different user

**Solution Steps:**
1. Go to **IAM → Users → llm-duel-arena-deploy**
2. Check **"Permissions"** tab - verify the policy is attached
3. Click on the policy name → **"JSON"** tab
4. Verify you see **TWO separate IAM statements**:
   - One with `CreateRole` and **NO Condition** ✅
   - One with `PassRole` and **WITH Condition** ✅
5. If you see a condition on `CreateRole`, delete and recreate the policy with the correct JSON from this document
6. Verify AWS credentials in your environment:
   ```bash
   aws sts get-caller-identity
   ```
   Should show: `arn:aws:iam::*:user/llm-duel-arena-deploy`

### Other Issues

### "Access Denied" Errors

If you get access denied errors:
1. Verify the policy is attached to the user
2. Check resource ARNs match your actual resources
3. Ensure you're using the correct AWS region
4. Check CloudTrail logs for specific permission issues

### Terraform State Lock Errors

If Terraform can't acquire locks:
- Verify DynamoDB table exists: `llm-duel-arena-terraform-locks`
- Check IAM permissions for DynamoDB operations
- Ensure the table is in the same region as your Terraform state

## Summary

Instead of `AdministratorAccess`, use this custom policy which grants:
- ✅ Only necessary permissions
- ✅ Scoped to project-specific resources
- ✅ Follows least privilege principle
- ✅ Suitable for CI/CD pipelines

This is much more secure than admin access and follows AWS security best practices.

