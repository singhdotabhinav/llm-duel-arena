# 🔄 CI/CD Pipeline Setup Guide

This guide explains how to set up and use the CI/CD pipeline for automated testing and deployment.

## 📋 Overview

The project includes two GitHub Actions workflows:

1. **`test.yml`** - Runs on every push and PR
   - Unit tests
   - Code quality checks (linting, formatting, type checking)
   - Security scanning

2. **`ci-cd.yml`** - Runs on push to main/develop branches
   - Full CI/CD pipeline
   - Builds Lambda packages
   - Deploys infrastructure (Terraform)
   - Deploys Lambda functions
   - Deploys static assets
   - Runs integration tests

## 🚀 Quick Start

### 1. Configure GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions → New repository secret

Add these secrets:

#### Required Secrets

```
AWS_ACCESS_KEY_ID          # AWS IAM user access key
AWS_SECRET_ACCESS_KEY      # AWS IAM user secret key
```

#### Optional Secrets (for notifications)

```
SLACK_WEBHOOK_URL          # Slack webhook for deployment notifications
DISCORD_WEBHOOK_URL        # Discord webhook for notifications
```

### 2. Set Up AWS IAM User

Create an IAM user with these permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "lambda:UpdateFunctionCode",
        "lambda:GetFunction",
        "lambda:ListFunctions",
        "s3:PutObject",
        "s3:GetObject",
        "s3:ListBucket",
        "s3:DeleteObject",
        "cloudfront:CreateInvalidation",
        "terraform:*",
        "dynamodb:*",
        "apigateway:*",
        "iam:*",
        "logs:*",
        "cloudwatch:*"
      ],
      "Resource": "*"
    }
  ]
}
```

**Or** attach these AWS managed policies:
- `AWSLambda_FullAccess`
- `AmazonS3FullAccess`
- `CloudFrontFullAccess`
- `AmazonAPIGatewayAdministrator`
- `AmazonDynamoDBFullAccess`
- `IAMFullAccess`
- `CloudWatchFullAccess`

### 3. Configure Environments

In GitHub repository → Settings → Environments:

#### Create `development` environment:
- **Name:** `development`
- **Deployment branches:** `develop`
- **Protection rules:** Optional (can require approval)

#### Create `production` environment:
- **Name:** `production`
- **Deployment branches:** `main`
- **Protection rules:** ✅ **Required reviewers** (recommended)
- **Wait timer:** Optional (e.g., 5 minutes delay)

## 📊 Workflow Details

### Test Workflow (`test.yml`)

**Triggers:**
- Push to `main` or `develop`
- Pull requests to `main` or `develop`
- Manual trigger (workflow_dispatch)

**Jobs:**
1. **Test** - Runs tests on Python 3.9, 3.10, 3.11
2. **Lint** - Code quality checks
3. **Security** - Security vulnerability scanning

**Duration:** ~5-10 minutes

### CI/CD Workflow (`ci-cd.yml`)

**Triggers:**
- Push to `main` (deploys to production)
- Push to `develop` (deploys to development)

**Jobs:**

1. **Test** (5-10 min)
   - Runs linter, formatter, type checker
   - Runs unit tests
   - Uploads coverage reports

2. **Build** (5-10 min)
   - Builds Lambda deployment packages
   - Uploads artifacts

3. **Deploy Infrastructure** (10-15 min)
   - Runs Terraform plan
   - Applies Terraform changes
   - Saves outputs

4. **Deploy Lambda** (5 min)
   - Downloads Lambda packages
   - Updates Lambda functions
   - Verifies deployment

5. **Deploy Static Assets** (3-5 min)
   - Uploads static files to S3
   - Invalidates CloudFront cache

6. **Integration Tests** (5 min)
   - Tests API endpoints
   - Tests frontend accessibility

7. **Notify** (1 min)
   - Sends deployment status notifications

**Total Duration:** ~35-50 minutes

## 🔧 Customization

### Modify Deployment Triggers

Edit `.github/workflows/ci-cd.yml`:

```yaml
on:
  push:
    branches:
      - main      # Change to your production branch
      - develop   # Change to your dev branch
  workflow_dispatch:  # Add manual trigger
    inputs:
      environment:
        description: 'Environment to deploy'
        required: true
        type: choice
        options:
          - dev
          - prod
```

### Add Slack Notifications

Add to `.github/workflows/ci-cd.yml` in the `notify` job:

```yaml
- name: Send Slack notification
  if: always()
  uses: slackapi/slack-github-action@v1
  with:
    webhook-url: ${{ secrets.SLACK_WEBHOOK_URL }}
    payload: |
      {
        "text": "Deployment ${{ job.status }}: ${{ github.ref }}",
        "blocks": [
          {
            "type": "section",
            "text": {
              "type": "mrkdwn",
              "text": "*Deployment Status:* ${{ job.status }}\n*Branch:* ${{ github.ref }}\n*Commit:* ${{ github.sha }}"
            }
          }
        ]
      }
```

### Add Email Notifications

Add to `.github/workflows/ci-cd.yml`:

```yaml
- name: Send email notification
  if: failure()
  uses: dawidd6/action-send-mail@v3
  with:
    server: smtp.gmail.com
    username: ${{ secrets.EMAIL_USERNAME }}
    password: ${{ secrets.EMAIL_PASSWORD }}
    to: your-email@example.com
    subject: "Deployment Failed: ${{ github.ref }}"
    body: "Deployment failed for commit ${{ github.sha }}"
```

## 🧪 Testing the Pipeline

### Test Locally

```bash
# Install act (GitHub Actions local runner)
brew install act  # macOS
# or
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Run test workflow locally
act -j test

# Run CI/CD workflow locally (requires AWS credentials)
act -j deploy-infrastructure --secret-file .secrets
```

### Test in GitHub

1. Create a test branch:
   ```bash
   git checkout -b test-ci-cd
   ```

2. Make a small change and push:
   ```bash
   echo "# Test" >> README.md
   git add README.md
   git commit -m "Test CI/CD"
   git push origin test-ci-cd
   ```

3. Create a PR to `develop` branch
4. Check Actions tab in GitHub to see workflow run

## 📈 Monitoring

### View Workflow Runs

1. Go to GitHub repository
2. Click **Actions** tab
3. Select workflow from left sidebar
4. Click on a run to see details

### View Logs

- Click on any job in the workflow run
- Expand steps to see logs
- Download logs for debugging

### Common Issues

#### AWS Credentials Error
```
Error: The security token included in the request is invalid
```
**Fix:** Verify `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` secrets are set correctly

#### Terraform Backend Error
```
Error: Failed to get existing workspaces
```
**Fix:** Ensure Terraform state bucket exists. Run `infrastructure/setup-state-bucket.sh`

#### Lambda Deployment Error
```
Error: Function not found
```
**Fix:** Ensure infrastructure is deployed first (Terraform apply)

## 🔐 Security Best Practices

1. **Never commit secrets** - Use GitHub Secrets
2. **Use least privilege IAM** - Only grant necessary permissions
3. **Enable branch protection** - Require PR reviews for production
4. **Use environment protection** - Require approval for production deployments
5. **Rotate credentials** - Regularly rotate AWS access keys
6. **Monitor access** - Review CloudTrail logs

## 📝 Workflow Status Badge

Add to your README.md:

```markdown
![CI/CD](https://github.com/your-username/llm-duel-arena/workflows/CI/CD%20Pipeline/badge.svg)
![Tests](https://github.com/your-username/llm-duel-arena/workflows/Test%20Suite/badge.svg)
```

## 🎯 Next Steps

1. ✅ Set up GitHub Secrets
2. ✅ Configure AWS IAM user
3. ✅ Create GitHub Environments
4. ✅ Test workflow with a test branch
5. ✅ Monitor first deployment
6. ✅ Set up notifications (optional)
7. ✅ Configure branch protection rules

## 📚 Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [AWS IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)

---

**Status:** ✅ CI/CD Pipeline Ready  
**Last Updated:** Current Session

