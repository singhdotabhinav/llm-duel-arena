# 🎯 Next Steps - Deployment Preparation

**Status:** ✅ CI/CD Pipeline Working  
**Next Priority:** 🔴 Phase 1 - Pre-Deployment Fixes

---

## ✅ What's Done

- ✅ CI/CD pipeline configured and working
- ✅ Code formatting (Black) passing
- ✅ Linting (flake8) passing
- ✅ Basic test structure in place
- ✅ Infrastructure code ready (Terraform)
- ✅ Lambda handlers implemented
- ✅ DynamoDB service created

---

## 🔴 CRITICAL - Phase 1: Pre-Deployment Fixes

**Estimated Time:** 1 week  
**Priority:** Must complete before deployment

### 1. Fix Session Cookie Issue (2-3 days) 🔴 BLOCKER

**Problem:** Session cookie not being sent back by browser after Cognito redirect.

**Solution:** Implement DynamoDB-backed sessions instead of cookies.

**Tasks:**
- [ ] Add session storage methods to `app/services/dynamodb_service.py`
  - `create_session(session_id, data, ttl)`
  - `get_session(session_id)`
  - `delete_session(session_id)`
- [ ] Update `app/routers/cognito_oidc_auth.py`:
  - Store session state in DynamoDB before redirect
  - Retrieve session from DynamoDB on callback
  - Use session ID in URL parameter or separate cookie
- [ ] Test full authentication flow
- [ ] Verify session persistence across redirects

**Files to Modify:**
- `app/services/dynamodb_service.py` - Add session methods
- `app/routers/cognito_oidc_auth.py` - Use DynamoDB sessions
- `app/core/config.py` - Add session table name config

---

### 2. Complete Database Migration (2-3 days) 🟡 HIGH PRIORITY

**Current State:** Some code still uses SQLAlchemy

**Tasks:**
- [ ] Audit all SQLAlchemy usage:
  ```bash
  grep -r "from.*database import\|from.*sqlalchemy\|db.query\|db.add\|db.commit" app/
  ```
- [ ] Migrate `app/routers/games.py` to DynamoDB
- [ ] Migrate `app/services/game_manager.py` to DynamoDB
- [ ] Remove SQLAlchemy imports
- [ ] Test all database operations
- [ ] Remove SQLAlchemy from `requirements.txt` (if not needed)

**Files to Check:**
- `app/routers/games.py`
- `app/services/game_manager.py`
- `app/services/game_db_service.py`
- Any other files using `db.query`, `db.add`, etc.

---

### 3. Environment Configuration (1 day) 🟡 HIGH PRIORITY

**Tasks:**
- [ ] Generate strong `APP_SECRET_KEY`:
  ```bash
  python3 -c "import secrets; print(secrets.token_urlsafe(32))"
  ```
- [ ] Create production `.env.example` with all required variables
- [ ] Document all environment variables in `ENV_VARIABLES.md`
- [ ] Set up AWS Secrets Manager integration (optional but recommended)
- [ ] Configure Cognito for production:
  - Create production User Pool
  - Create production App Client
  - Set callback URLs
  - Enable required scopes

**Required Environment Variables:**
```
APP_SECRET_KEY=<strong-random-key>
DEPLOYMENT_MODE=aws
USE_COGNITO=true
COGNITO_USER_POOL_ID=<prod-pool-id>
COGNITO_CLIENT_ID=<prod-client-id>
COGNITO_REGION=us-east-1
COGNITO_CALLBACK_URL=https://yourdomain.com/auth/callback
CORS_ORIGINS=https://yourdomain.com
ALLOWED_REDIRECT_URIS=https://yourdomain.com/auth/callback
DYNAMODB_TABLE_NAME=llm-duel-arena-users-prod
```

---

## 🏗️ Phase 2: Infrastructure Setup (After Phase 1)

**Estimated Time:** 2-3 days  
**Priority:** Can start after Phase 1 is complete

### 1. AWS Account Setup (30 minutes)

- [ ] Create/verify AWS account
- [ ] Configure AWS CLI: `aws configure`
- [ ] Set up billing alerts
- [ ] Create IAM user for deployment (or use existing)

### 2. Terraform State Backend (30 minutes)

```bash
cd infrastructure
./setup-state-bucket.sh us-east-1
```

### 3. Terraform Configuration (1 hour)

- [ ] Copy `terraform.tfvars.example` to `terraform.tfvars`
- [ ] Fill in all required values
- [ ] Review resource sizes

### 4. Deploy Infrastructure (1-2 hours)

```bash
cd infrastructure/environments/dev
terraform init
terraform plan -var-file=terraform.tfvars
terraform apply -var-file=terraform.tfvars
```

---

## 🚀 Quick Start Guide

### Option 1: Start with Phase 1 (Recommended)

**Focus on fixing the critical blockers first:**

1. **Fix Session Cookie Issue** (Most Critical)
   - This blocks authentication
   - Without this, users can't log in
   - Start here: `app/services/dynamodb_service.py`

2. **Complete Database Migration**
   - Ensures all code uses DynamoDB
   - Prevents runtime errors in production
   - Start here: Audit SQLAlchemy usage

3. **Environment Configuration**
   - Prepares for production deployment
   - Ensures all secrets are configured
   - Start here: Generate `APP_SECRET_KEY`

### Option 2: Set Up Infrastructure First

**If you want to test infrastructure:**

1. Set up AWS account
2. Configure Terraform
3. Deploy to dev environment
4. Test basic endpoints
5. Then fix Phase 1 issues

---

## 📋 Recommended Order

1. **Week 1: Fix Critical Issues**
   - Day 1-2: Fix session cookie issue
   - Day 3-4: Complete database migration
   - Day 5: Environment configuration

2. **Week 2: Infrastructure & Deployment**
   - Day 1: AWS setup & Terraform state
   - Day 2: Deploy infrastructure
   - Day 3: Deploy Lambda functions
   - Day 4: Deploy static assets
   - Day 5: End-to-end testing

3. **Week 3: Production & Monitoring**
   - Day 1-2: Production deployment
   - Day 3: Monitoring setup
   - Day 4: Documentation
   - Day 5: Final testing

---

## 🎯 Immediate Next Action

**Start with:** Fix Session Cookie Issue

**Why:** This is blocking authentication, which is critical for the app.

**How:**
1. Open `app/services/dynamodb_service.py`
2. Add session storage methods
3. Update `app/routers/cognito_oidc_auth.py` to use DynamoDB sessions
4. Test locally

**Files to start with:**
- `app/services/dynamodb_service.py`
- `app/routers/cognito_oidc_auth.py`
- `app/core/config.py`

---

## 📚 Resources

- **Deployment Roadmap:** `DEPLOYMENT_ROADMAP.md`
- **Deployment Checklist:** `DEPLOYMENT_CHECKLIST.md`
- **Project Status:** `PROJECT_STATUS.md`
- **CI/CD Setup:** `CI_CD_SETUP.md`

---

## 💡 Tips

1. **Test Locally First:** Always test changes locally before deploying
2. **Use Dev Environment:** Deploy to dev before production
3. **Monitor Costs:** Set up billing alerts early
4. **Document Changes:** Update docs as you make changes
5. **Commit Often:** Small, focused commits are easier to debug

---

**Ready to start?** Begin with fixing the session cookie issue! 🚀

