# CI/CD Workflow Behavior Guide

## Overview

This document explains when each job in the CI/CD pipeline runs and why.

## Workflow Triggers

The pipeline runs on:
- **Push** to `main` or `develop` branches
- **Pull Request** targeting `main` or `develop` branches

## Job Execution Matrix

| Job | Pull Request | Push to develop | Push to main |
|-----|--------------|-----------------|--------------|
| **test** | ✅ Runs | ✅ Runs | ✅ Runs |
| **build** | ✅ Runs | ✅ Runs | ✅ Runs |
| **deploy-infrastructure** | ❌ Skipped | ✅ Runs | ✅ Runs |
| **deploy-lambda** | ❌ Skipped | ✅ Runs | ✅ Runs |
| **deploy-static** | ❌ Skipped | ✅ Runs | ✅ Runs |
| **integration-test** | ❌ Skipped | ✅ Runs | ✅ Runs |
| **notify** | ❌ Skipped | ✅ Runs | ✅ Runs |

## Detailed Job Behavior

### 1. Test Job (`test`)
**Runs on:** All events (PRs and pushes)

**Purpose:** 
- Run linting (flake8)
- Check code formatting (black)
- Run type checking (mypy)
- Execute unit tests (pytest)
- Generate coverage reports

**Why always runs:** Ensures code quality before merging or deploying.

---

### 2. Build Job (`build`)
**Runs on:** All events (PRs and pushes)

**Purpose:**
- Build Lambda deployment packages
- Verify packages can be created successfully
- Upload packages as artifacts

**Why runs on PRs:** Validates that Lambda packages build correctly before merging, catching build issues early.

**Environment:** 
- PRs: Uses `int` environment (default)
- Pushes: Uses `prod` for main, `int` for develop

---

### 3. Deploy Infrastructure (`deploy-infrastructure`)
**Runs on:** Only pushes to `main` or `develop`

**Condition:** `if: github.event_name == 'push' && (github.ref == 'refs/heads/main' || github.ref == 'refs/heads/develop')`

**Purpose:**
- Initialize Terraform
- Plan infrastructure changes
- Apply infrastructure changes (auto-approve)
- Save Terraform outputs

**Why skipped on PRs:** 
- Security: Prevents deploying infrastructure from untrusted PRs
- Cost: Avoids creating AWS resources for every PR
- Safety: Only deploy after code is reviewed and merged

---

### 4. Deploy Lambda Functions (`deploy-lambda`)
**Runs on:** Only pushes to `main` or `develop`

**Condition:** `if: github.event_name == 'push' && (github.ref == 'refs/heads/main' || github.ref == 'refs/heads/develop')`

**Purpose:**
- Update Lambda function code
- Deploy new versions of Lambda functions

**Why skipped on PRs:** Same as deploy-infrastructure - security and safety.

---

### 5. Deploy Static Assets (`deploy-static`)
**Runs on:** Only pushes to `main` or `develop`

**Condition:** `if: github.event_name == 'push' && (github.ref == 'refs/heads/main' || github.ref == 'refs/heads/develop')`

**Purpose:**
- Sync static files to S3
- Invalidate CloudFront cache

**Why skipped on PRs:** Same as other deployment jobs.

---

### 6. Integration Tests (`integration-test`)
**Runs on:** Only pushes to `main` or `develop`

**Condition:** `if: github.event_name == 'push' && (github.ref == 'refs/heads/main' || github.ref == 'refs/heads/develop')`

**Purpose:**
- Test API endpoints after deployment
- Verify frontend accessibility
- Validate deployment success

**Why skipped on PRs:** Requires deployed infrastructure to test against.

---

### 7. Notify Deployment Status (`notify`)
**Runs on:** Only pushes to `main` or `develop`

**Condition:** `if: always() && github.event_name == 'push'`

**Purpose:**
- Send deployment success/failure notifications
- Log deployment status

**Why skipped on PRs:** Only relevant after actual deployments.

## Environment Mapping

| Branch | Environment | AWS Resources |
|--------|-------------|---------------|
| `main` | `production` | Production AWS resources |
| `develop` | `integration` | Integration/staging AWS resources |
| PRs | `int` (build only) | No AWS resources created |

## Why This Design?

### Security Best Practices
- ✅ PRs cannot deploy to AWS (prevents malicious code deployment)
- ✅ Only merged code deploys (code review required)
- ✅ Separate environments for dev/prod

### Cost Optimization
- ✅ No AWS resources created for PRs (saves money)
- ✅ Only deploy when code is merged
- ✅ Build verification without deployment costs

### Developer Experience
- ✅ Fast feedback on PRs (tests + build)
- ✅ Catch issues before merging
- ✅ Verify builds work before deployment

## Workflow Flow Diagram

```
Pull Request:
  test → build → (stop, no deployment)

Push to develop:
  test → build → deploy-infrastructure → deploy-lambda → deploy-static → integration-test → notify

Push to main:
  test → build → deploy-infrastructure → deploy-lambda → deploy-static → integration-test → notify
```

## Troubleshooting

### "Why isn't my deployment job running?"
- Check if you're pushing to `main` or `develop` (not a PR)
- Verify the branch name matches exactly
- Check workflow logs for skipped job messages

### "Why does build run but not deploy?"
- This is expected behavior for PRs
- Build verifies packages can be created
- Deployment only happens after merge

### "Can I force a deployment?"
- Push directly to `main` or `develop` (not recommended)
- Or merge your PR, which will trigger deployment

## Related Documentation

- `CI_CD_AUTOMATION.md` - How automation works
- `AWS_IAM_PERMISSIONS.md` - Required AWS permissions
- `.github/workflows/ci-cd.yml` - Full workflow configuration

