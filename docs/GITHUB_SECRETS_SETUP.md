# GitHub Secrets Setup Guide

## Overview

Your CI/CD pipeline requires AWS credentials to deploy infrastructure. These credentials are stored as GitHub Secrets to keep them secure.

## Required Secrets

Based on your `.github/workflows/ci-cd.yml`, you need to add:

1. `AWS_ACCESS_KEY_ID` - Your AWS Access Key ID
2. `AWS_SECRET_ACCESS_KEY` - Your AWS Secret Access Key

## Step-by-Step: Adding Secrets to GitHub

### Method 1: Using GitHub Web Interface (Recommended)

1. **Navigate to Your Repository**
   - Go to your GitHub repository: `https://github.com/YOUR_USERNAME/llm-duel-arena`
   - Make sure you're logged in and have admin/owner permissions

2. **Open Repository Settings**
   - Click on the **"Settings"** tab (top navigation bar)
   - If you don't see "Settings", you may not have admin access

3. **Go to Secrets and Variables**
   - In the left sidebar, click **"Secrets and variables"**
   - Then click **"Actions"**

4. **Add AWS Access Key ID**
   - Click **"New repository secret"** button
   - **Name**: `AWS_ACCESS_KEY_ID`
   - **Secret**: Paste your AWS Access Key ID (e.g., `AKIAIOSFODNN7EXAMPLE`)
   - Click **"Add secret"**

5. **Add AWS Secret Access Key**
   - Click **"New repository secret"** button again
   - **Name**: `AWS_SECRET_ACCESS_KEY`
   - **Secret**: Paste your AWS Secret Access Key (e.g., `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY`)
   - Click **"Add secret"**

6. **Verify Secrets**
   - You should now see both secrets listed (values will be hidden)
   - They will be available to your GitHub Actions workflows

### Method 2: Using GitHub CLI

If you have GitHub CLI installed:

```bash
# Set AWS Access Key ID
gh secret set AWS_ACCESS_KEY_ID --body "YOUR_ACCESS_KEY_ID"

# Set AWS Secret Access Key
gh secret set AWS_SECRET_ACCESS_KEY --body "YOUR_SECRET_ACCESS_KEY"

# Verify secrets are set
gh secret list
```

### Method 3: Using GitHub API

```bash
# Set AWS_ACCESS_KEY_ID
curl -X POST \
  -H "Authorization: token YOUR_GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/YOUR_USERNAME/llm-duel-arena/actions/secrets/AWS_ACCESS_KEY_ID \
  -d '{"encrypted_value":"YOUR_ENCRYPTED_VALUE","key_id":"YOUR_KEY_ID"}'

# Note: GitHub API requires encryption - use Method 1 or 2 instead
```

## Visual Guide

```
GitHub Repository
├── Settings (top navigation)
    ├── Secrets and variables (left sidebar)
        └── Actions
            ├── New repository secret (button)
            │   ├── Name: AWS_ACCESS_KEY_ID
            │   └── Secret: [your access key]
            └── New repository secret (button)
                ├── Name: AWS_SECRET_ACCESS_KEY
                └── Secret: [your secret key]
```

## Environment-Specific Secrets (Optional)

If you want different credentials for different environments (dev/int/prod), you can use GitHub Environments:

1. **Go to Environments**
   - Settings → Environments → New environment
   - Create environments: `integration`, `production`

2. **Add Secrets to Each Environment**
   - Click on each environment
   - Add `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`
   - Update your workflow to use environment secrets

3. **Update Workflow** (if needed)
   ```yaml
   environment: ${{ github.ref == 'refs/heads/main' && 'production' || 'integration' }}
   ```

## Security Best Practices

1. ✅ **Never commit secrets to git** - Always use GitHub Secrets
2. ✅ **Use separate IAM users** - Create different users for dev/int/prod
3. ✅ **Rotate keys regularly** - Change access keys every 90 days
4. ✅ **Use least privilege** - Only grant necessary permissions
5. ✅ **Monitor usage** - Enable CloudTrail to audit API calls
6. ✅ **Restrict access** - Only repository admins should manage secrets

## Verifying Secrets Work

After adding secrets, trigger a workflow run:

1. **Push a commit** to `main` or `develop` branch
2. **Go to Actions tab** in GitHub
3. **Check workflow run** - It should use your secrets automatically
4. **Look for errors** - If secrets are missing, you'll see an error like:
   ```
   Error: Missing required input: aws-access-key-id
   ```

## Troubleshooting

### "Settings tab not visible"
- You need admin/owner permissions on the repository
- Ask repository owner to add you as collaborator with admin access

### "Secret not found in workflow"
- Verify secret name matches exactly: `AWS_ACCESS_KEY_ID` (case-sensitive)
- Check workflow file uses: `${{ secrets.AWS_ACCESS_KEY_ID }}`
- Ensure workflow has permission to read secrets

### "Access denied" in workflow
- Verify AWS credentials are correct
- Check IAM user has necessary permissions (see `AWS_IAM_PERMISSIONS.md`)
- Ensure AWS region matches (`us-east-1` in your workflow)

### "Invalid credentials"
- Double-check you copied the full access key and secret key
- Ensure no extra spaces or newlines
- Verify keys haven't expired or been rotated

## Quick Reference

**Repository URL Pattern:**
```
https://github.com/YOUR_USERNAME/llm-duel-arena/settings/secrets/actions
```

**Direct Navigation:**
1. Repository → Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`

## Next Steps

After adding secrets:
1. ✅ Verify secrets are set correctly
2. ✅ Test workflow by pushing to `develop` branch
3. ✅ Monitor first deployment in Actions tab
4. ✅ Check AWS resources are created successfully

For IAM permissions, see: `AWS_IAM_PERMISSIONS.md`

