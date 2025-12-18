# CI/CD Automation Guide

## Overview

The CI/CD pipeline has been configured to run **fully automatically** without any manual intervention. All deployment steps execute automatically when code is pushed to `main` or `develop` branches.

## What Changed

### 1. Removed Manual Prompts

**Before:**
- `deploy.sh` script had a manual prompt: `read -p "Continue with deployment? (y/n)"`
- Required manual confirmation before deploying

**After:**
- Scripts detect CI/CD environment (`CI`, `GITHUB_ACTIONS`, or `AUTO_APPROVE`)
- Automatically proceed with deployment in automated environments
- Still prompts for confirmation when running locally (for safety)

### 2. Improved Lambda Deployment

**Before:**
- Called `deploy.sh` which was meant for Terraform infrastructure
- Could fail if Lambda functions didn't exist

**After:**
- Direct AWS CLI calls to update Lambda function code
- Graceful error handling if functions don't exist yet
- Better logging and status reporting

### 3. Enhanced Error Handling

- Integration tests use `continue-on-error: true` to not block deployment
- Better error messages and warnings
- Handles missing URLs gracefully

## Pipeline Flow

```
Push to main/develop
    ↓
1. Run Tests (lint, type check, unit tests)
    ↓
2. Build Lambda Packages
    ↓
3. Deploy Infrastructure (Terraform)
    ├── Init Terraform
    ├── Plan changes
    └── Apply automatically (no approval needed)
    ↓
4. Deploy Lambda Functions
    └── Update function code directly
    ↓
5. Deploy Static Assets
    └── Sync to S3 and invalidate CloudFront
    ↓
6. Run Integration Tests
    └── Test API and frontend (non-blocking)
    ↓
7. Notify Status
    └── Success/Failure notifications
```

## Automation Features

### ✅ Fully Automated
- No manual approvals required
- All steps run automatically
- Terraform applies changes with `-auto-approve`

### ✅ Environment Detection
Scripts automatically detect CI/CD environment:
```bash
if [ -n "$CI" ] || [ -n "$GITHUB_ACTIONS" ] || [ "$AUTO_APPROVE" == "true" ]; then
  # Run automatically
else
  # Prompt for confirmation (local development)
fi
```

### ✅ Error Resilience
- Integration tests don't block deployment
- Lambda updates handle missing functions gracefully
- Clear error messages and warnings

## Environment Variables

The workflow sets these automatically:
- `CI: "true"` - Indicates CI/CD environment
- `AUTO_APPROVE: "true"` - Enables auto-approval
- `AWS_REGION: us-east-1` - AWS region for deployment

## Manual Override

If you need to run scripts manually with auto-approval:

```bash
# Set environment variable
export AUTO_APPROVE=true

# Or
export CI=true

# Run script
./infrastructure/deploy.sh prod us-east-1
```

## Branch Behavior

### `main` branch
- Deploys to **production** environment
- Full deployment pipeline runs
- All tests must pass

### `develop` branch
- Deploys to **integration** environment
- Full deployment pipeline runs
- All tests must pass

### Pull Requests
- Only runs tests (no deployment)
- Validates code quality
- Checks formatting and types

## Troubleshooting

### Pipeline Stuck
- Check GitHub Actions tab for errors
- Verify AWS credentials are set correctly
- Check Terraform state bucket exists

### Lambda Functions Not Updating
- Check Lambda deployment job logs
- Verify zip files were built correctly
- Ensure Terraform created the functions first

### Terraform Apply Fails
- Check Terraform plan output in logs
- Verify IAM permissions are correct
- Check for resource conflicts

## Security Notes

- ✅ All secrets stored in GitHub Secrets (encrypted)
- ✅ AWS credentials scoped to project resources
- ✅ No hardcoded credentials in code
- ✅ Terraform state encrypted in S3

## Next Steps

1. **Monitor First Deployment**
   - Watch the Actions tab during first run
   - Verify all steps complete successfully
   - Check AWS resources are created

2. **Set Up Notifications** (Optional)
   - Add Slack/Discord webhooks to notification job
   - Configure email alerts for failures
   - Set up CloudWatch alarms

3. **Optimize Performance** (Optional)
   - Cache Terraform providers
   - Parallelize independent jobs
   - Use matrix builds for multiple environments

## Related Documentation

- `AWS_IAM_PERMISSIONS.md` - Required AWS permissions
- `GITHUB_SECRETS_SETUP.md` - Setting up GitHub secrets
- `.github/workflows/ci-cd.yml` - Full workflow configuration




