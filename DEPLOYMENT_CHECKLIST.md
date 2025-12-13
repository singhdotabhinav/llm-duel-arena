# 🚀 Quick Deployment Checklist

**Use this checklist alongside the full roadmap (`DEPLOYMENT_ROADMAP.md`)**

---

## 🔴 CRITICAL - Must Fix Before Deployment

### Phase 1: Pre-Deployment Fixes

- [ ] **Fix Session Cookie Issue** (2-3 days)
  - [ ] Implement DynamoDB session storage
  - [ ] Update `app/services/dynamodb_service.py` with session methods
  - [ ] Update `app/routers/cognito_oidc_auth.py` to use DynamoDB sessions
  - [ ] Test full authentication flow
  - [ ] Verify session persistence

- [ ] **Complete Database Migration** (2-3 days)
  - [ ] Audit all SQLAlchemy usage
  - [ ] Migrate `app/routers/games.py` to DynamoDB
  - [ ] Migrate `app/services/game_manager.py` to DynamoDB
  - [ ] Remove SQLAlchemy dependencies
  - [ ] Test all database operations

- [ ] **Environment Configuration** (1 day)
  - [ ] Generate strong `APP_SECRET_KEY`
  - [ ] Configure Cognito for production
  - [ ] Set up AWS Secrets Manager
  - [ ] Update all environment variables
  - [ ] Create production `.env.example`

---

## 🏗️ Infrastructure Setup

### Phase 2: AWS Setup

- [ ] **AWS Account**
  - [ ] Create/verify AWS account
  - [ ] Configure AWS CLI (`aws configure`)
  - [ ] Set up billing alerts
  - [ ] Create IAM user for deployment

- [ ] **Terraform State**
  - [ ] Run `infrastructure/setup-state-bucket.sh`
  - [ ] Verify S3 bucket created
  - [ ] Verify DynamoDB lock table created

- [ ] **Terraform Configuration**
  - [ ] Copy `terraform.tfvars.example` to `terraform.tfvars`
  - [ ] Fill in all required values
  - [ ] Review resource sizes

- [ ] **Deploy Infrastructure**
  - [ ] Run `terraform init`
  - [ ] Run `terraform plan`
  - [ ] Run `terraform apply`
  - [ ] Save outputs

---

## 🔧 Application Deployment

### Phase 3: Deploy Application

- [ ] **Build Lambda Packages**
  - [ ] Run `infrastructure/build-lambda.sh prod`
  - [ ] Verify package sizes
  - [ ] Check for errors

- [ ] **Deploy Lambda Functions**
  - [ ] Run `infrastructure/deploy.sh prod us-east-1`
  - [ ] Verify deployment success
  - [ ] Check function configurations

- [ ] **Deploy Static Assets**
  - [ ] Run `infrastructure/deploy-static.sh prod us-east-1`
  - [ ] Verify assets accessible
  - [ ] Check CloudFront cache

- [ ] **Configure Environment Variables**
  - [ ] Set Lambda environment variables
  - [ ] Configure Secrets Manager
  - [ ] Update OAuth redirect URIs

---

## 🧪 Testing

### Phase 4: Validation

- [ ] **API Testing**
  - [ ] Test game creation endpoint
  - [ ] Test game state retrieval
  - [ ] Test move execution
  - [ ] Test authentication endpoints

- [ ] **Authentication Testing**
  - [ ] Test Cognito login flow
  - [ ] Verify session persistence
  - [ ] Test logout functionality
  - [ ] Verify user info retrieval

- [ ] **Frontend Testing**
  - [ ] All game types load
  - [ ] API calls work
  - [ ] No console errors
  - [ ] Static assets load

---

## 🔐 Security

### Phase 5: Security Hardening

- [ ] **Security Configuration**
  - [ ] Review IAM policies
  - [ ] Enable DynamoDB encryption
  - [ ] Enable point-in-time recovery
  - [ ] Configure CloudFront security headers
  - [ ] Set up WAF (optional)

- [ ] **Secrets Management**
  - [ ] Create Secrets Manager secrets
  - [ ] Update Lambda to use secrets
  - [ ] Remove API keys from env vars

- [ ] **Production Settings**
  - [ ] `https_only=True` for cookies
  - [ ] CORS origins set correctly
  - [ ] Rate limiting enabled
  - [ ] Security headers configured

---

## 📊 Monitoring

### Phase 6: Monitoring Setup

- [ ] **CloudWatch**
  - [ ] Create dashboard
  - [ ] Set up error alarms
  - [ ] Set up billing alarms
  - [ ] Configure log retention

- [ ] **SNS Notifications**
  - [ ] Create SNS topic
  - [ ] Subscribe email addresses
  - [ ] Configure alarms
  - [ ] Test notifications

---

## 🚀 Launch

### Phase 7: Go Live

- [ ] **Pre-Launch Checklist**
  - [ ] All previous phases complete
  - [ ] All tests passing
  - [ ] Security review done
  - [ ] Monitoring configured
  - [ ] Rollback plan ready

- [ ] **Deploy**
  - [ ] Final infrastructure deployment
  - [ ] Deploy Lambda functions
  - [ ] Deploy static assets
  - [ ] Verify endpoints

- [ ] **Post-Launch**
  - [ ] Monitor dashboards hourly (first 24h)
  - [ ] Check for errors
  - [ ] Monitor costs
  - [ ] Collect user feedback

---

## 🔄 CI/CD Setup

### Phase 8: CI/CD Configuration

- [ ] **Run CI/CD Setup Script** (15 minutes)
  - [ ] Run `./setup-cicd.sh`
  - [ ] Create IAM user for CI/CD
  - [ ] Generate access keys
  - [ ] Save credentials securely

- [ ] **Configure GitHub Secrets** (5 minutes)
  - [ ] Go to Repository → Settings → Secrets → Actions
  - [ ] Add `AWS_ACCESS_KEY_ID`
  - [ ] Add `AWS_SECRET_ACCESS_KEY`

- [ ] **Create GitHub Environments** (5 minutes)
  - [ ] Go to Repository → Settings → Environments
  - [ ] Create `development` environment
  - [ ] Create `production` environment
  - [ ] Add protection rules for production

- [ ] **Test CI/CD Pipeline** (10 minutes)
  - [ ] Create test branch
  - [ ] Push changes
  - [ ] Create PR to `develop`
  - [ ] Verify workflow runs successfully

## 📝 Quick Commands Reference

```bash
# CI/CD Setup
./setup-cicd.sh              # Interactive setup script

# AWS Setup
aws sts get-caller-identity  # Verify access
aws configure                # Configure CLI

# Terraform State
cd infrastructure
./setup-state-bucket.sh us-east-1

# Terraform Deployment
cd infrastructure/environments/prod
terraform init
terraform plan -var-file=terraform.tfvars
terraform apply -var-file=terraform.tfvars
terraform output > outputs.txt

# Lambda Deployment
cd infrastructure
./build-lambda.sh prod
./deploy.sh prod us-east-1

# Static Assets
./deploy-static.sh prod us-east-1

# Monitoring
aws logs tail /aws/lambda/llm-duel-arena-game-prod --follow

# Test CI/CD
git checkout -b test-ci-cd
echo "# Test" >> README.md
git add README.md && git commit -m "Test CI/CD"
git push origin test-ci-cd
# Create PR to develop branch
```

---

## 🎯 Success Criteria

Before going live, ensure:
- ✅ Authentication works end-to-end
- ✅ All API endpoints functional
- ✅ Frontend loads without errors
- ✅ Monitoring configured
- ✅ Security best practices implemented
- ✅ Billing alerts set up

---

**Next Step:** Start with Phase 1.1 - Fix Session Cookie Issue

