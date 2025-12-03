# Security Deployment Guide

Comprehensive security guide for deploying LLM Duel Arena to production.

## 🔐 Pre-Deployment Security Checklist

### Critical Items (Must Do)

- [ ] **Generate Strong Secret Key**
  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(32))"
  ```
  Set as `APP_SECRET_KEY` in production environment

- [ ] **Set Production Environment Variables**
  - `DEPLOYMENT_MODE=aws`
  - `LOG_LEVEL=INFO` or `WARNING`
  - `USE_DYNAMODB_SESSIONS=true`
  - `ENABLE_RATE_LIMITING=true`

- [ ] **Configure CORS**
  - Set `CORS_ORIGINS` to your production domain only
  - Example: `CORS_ORIGINS=https://yourdomain.com`
  - Never use wildcard (*) in production

- [ ] **OAuth Redirect URI Whitelist**
  - Update `ALLOWED_REDIRECT_URIS` with production callback URL
  - Example: `https://yourdomain.com/auth/callback`
  - Update OAuth provider (Google/Cognito) configuration to match

- [ ] **API Keys Security**
  - Option 1: Use AWS Secrets Manager (recommended)
    - Set `USE_SECRETS_MANAGER=true`
    - Store keys in Secrets Manager with prefix `llm-duel-arena/`
  - Option 2: Use environment variables (less secure)
    - Ensure keys are not committed to Git
    - Use AWS Parameter Store or manual configuration

### High Priority

- [ ] **AWS IAM Configuration**
  - Lambda should use IAM roles (configured in template.yaml) ✅
  - Never use `AWS_ACCESS_KEY_ID` in production
  - Review Lambda IAM policies for least privilege

- [ ] **HTTPS Configuration**
  - Obtain SSL certificate (AWS Certificate Manager)
  - Configure custom domain with API Gateway
  - Ensure `https_only=True` for session cookies (automatic in production)

- [ ] **Billing Alarms**
  - CloudWatch billing alarm configured in template.yaml ✅
  - Set up SNS topic for alarm notifications
  - Configure alarm threshold (default: $10 USD)

- [ ] **DynamoDB Security**
  - Point-in-time recovery enabled ✅
  - KMS encryption enabled ✅
  - Review backup retention policies

### Medium Priority

- [ ] **Rate Limiting Configuration**
  - Review default rate limits:
    - Game creation: 10/minute per IP
    - Move execution: 30/minute per IP (in code)
    - API Gateway throttling: 10 req/s, 20 burst ✅
  - Adjust limits based on expected traffic

- [ ] **Monitoring & Logging**
  - Enable CloudWatch detailed monitoring
  - Set up CloudWatch dashboards for key metrics
  - Configure log retention (default: 14 days) ✅
  - Review logs for sensitive data leakage

- [ ] **AWS WAF (Optional)**
  - Deploy WAF for DDoS protection
  - See [AWS WAF Setup](#aws-waf-setup) section below

---

## 📋 Deployment Steps

### 1. Prepare Local Environment

```bash
# Clone repository
cd /path/to/llm-duel-arena

# Create .env file from example
cp .env.example .env

# Generate secret key and update .env
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Set production values in .env
DEPLOYMENT_MODE=aws
USE_DYNAMODB_SESSIONS=true
CORS_ORIGINS=https://yourdomain.com
```

### 2. Configure AWS Credentials

```bash
# Configure AWS CLI (use your production account)
aws configure

# Verify credentials
aws sts get-caller-identity
```

### 3. Build and Deploy with SAM

```bash
# Install dependencies
pip install -r requirements.txt

# Build Lambda package
sam build

# Deploy to AWS (guided mode for first deployment)
sam deploy --guided
```

During guided deployment:
- Stack Name: `llm-duel-arena-prod`
- AWS Region: `us-east-1` (or your preferred region)
- Confirm changes: Yes
- Allow SAM CLI IAM role creation: Yes
- Save configuration: Yes

### 4. Post-Deployment Configuration

```bash
# Get API Gateway URL from deployment output
API_URL=$(aws cloudformation describe-stacks \
  --stack-name llm-duel-arena-prod \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
  --output text)

echo "API URL: $API_URL"

# Update OAuth provider redirect URIs
# - Go to Google Cloud Console or AWS Cognito
# - Add: ${API_URL}/auth/callback
```

### 5. Configure Custom Domain (Recommended)

```bash
# Create SSL certificate in AWS Certificate Manager
aws acm request-certificate \
  --domain-name yourdomain.com \
  --validation-method DNS

# Associate custom domain with API Gateway
# (Use AWS Console or CloudFormation)

# Update CORS_ORIGINS and ALLOWED_REDIRECT_URIS
```

---

## 🔑 AWS Secrets Manager Setup (Optional)

Using Secrets Manager provides better security for API keys.

### Create Secrets

```bash
# OpenAI API Key
aws secretsmanager create-secret \
  --name llm-duel-arena/openai-api-key \
  --secret-string "your-openai-api-key"

# Anthropic API Key
aws secretsmanager create-secret \
  --name llm-duel-arena/anthropic-api-key \
  --secret-string "your-anthropic-api-key"

# HuggingFace Token
aws secretsmanager create-secret \
  --name llm-duel-arena/huggingface-token \
  --secret-string "your-huggingface-token"
```

### Update Lambda Environment

```bash
# Set in CloudFormation parameters or environment variables
USE_SECRETS_MANAGER=true
SECRETS_MANAGER_PREFIX=llm-duel-arena
```

### Costs

- $0.40/month per secret
- $0.05 per 10,000 API calls
- Minimal cost for enhanced security

---

## 🛡️ AWS WAF Setup (Optional)

AWS WAF provides DDoS protection and advanced rate limiting.

### Create WAF Web ACL

1. Go to AWS WAF console
2. Create Web ACL for regional resources (API Gateway)
3. Add rules:
   - IP rate limiting (2000 requests per 5 minutes)
   - Geographic restrictions (if applicable)
   - SQL injection protection
   - XSS protection

### Associate with API Gateway

```bash
# Get API Gateway ARN
API_ARN=$(aws apigatewayv2 get-apis \
  --query "Items[?Name=='llm-duel-arena'].ApiId" \
  --output text)

# Associate WAF
aws wafv2 associate-web-acl \
  --web-acl-arn <your-waf-arn> \
  --resource-arn "arn:aws:apigateway:region::/apis/${API_ARN}/stages/$default"
```

### Costs

- $5/month per Web ACL
- $1/month per rule
- $0.60 per million requests

---

## 📊 Monitoring & Alerts

### CloudWatch Dashboards

Create dashboard with:
- Lambda invocation count
- Lambda errors
- API Gateway 4xx/5xx errors
- DynamoDB read/write capacity
- Estimated charges

### SNS Topic for Alarms

```bash
# Create SNS topic
aws sns create-topic --name llm-duel-arena-alerts

# Subscribe email
aws sns subscribe \
  --topic-arn arn:aws:sns:region:account:llm-duel-arena-alerts \
  --protocol email \
  --notification-endpoint your-email@example.com

# Update BillingAlarm in template.yaml to use this topic
```

---

## 🚨 Incident Response

### High AWS Costs Detected

1. Check CloudWatch metrics for unusual traffic
2. Review API Gateway access logs
3. Temporarily disable API Gateway if under attack
4. Review and tighten rate limits
5. Enable AWS WAF if not already enabled

### Authentication Bypass Attempt

1. Review CloudWatch logs for suspicious activity
2. Rotate `APP_SECRET_KEY` immediately
3. Invalidate all active sessions
4. Review and update OAuth redirect URI whitelist

### Data Breach

1. Rotate all API keys (OpenAI, Anthropic, HuggingFace)
2. Review DynamoDB access logs
3. Enable CloudTrail if not already enabled
4. Review IAM policies for excessive permissions

---

## 🔄 Regular Maintenance

### Weekly
- Review CloudWatch logs for errors
- Check billing dashboard
- Monitor rate limiting effectiveness

### Monthly
- Review IAM policies
- Update dependencies (`pip list --outdated`)
- Review and clean up old DynamoDB sessions

### Quarterly
- Rotate API keys
- Review security configurations
- Test disaster recovery procedures
- Update this security guide

---

## 📚 Additional Resources

- [AWS Lambda Security Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/lambda-security.html)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [AWS Well-Architected Framework - Security Pillar](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/welcome.html)
- [FastAPI Security Documentation](https://fastapi.tiangolo.com/tutorial/security/)
