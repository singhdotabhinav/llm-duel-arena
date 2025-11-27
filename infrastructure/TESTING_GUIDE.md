# Testing Guide

This guide covers testing the LLM Duel Arena application both locally and in AWS.

## Pre-Deployment Testing

### 1. Test Local Application

Test that the FastAPI application works locally before deploying to AWS:

```bash
cd infrastructure
./test-local.sh
```

This will:
- ✅ Check Python dependencies
- ✅ Test imports
- ✅ Validate configuration
- ✅ Check Ollama connection (if running)

**Start local server:**
```bash
cd ..
source venv/bin/activate
uvicorn app.main:app --reload
```

Visit `http://localhost:8000` and test:
- [ ] Landing page loads
- [ ] Game creation works
- [ ] Models can make moves
- [ ] Authentication works (if configured)
- [ ] Game history saves

### 2. Test Deployment Configuration

Before deploying to AWS, validate your Terraform configuration:

```bash
cd infrastructure
./test-deployment.sh dev
```

This will check:
- ✅ Prerequisites installed (Terraform, AWS CLI, Python)
- ✅ AWS credentials configured
- ✅ Environment structure correct
- ✅ Terraform modules present
- ✅ Application code exists
- ✅ Deployment scripts available
- ✅ Terraform configuration valid

### 3. Test Terraform Plan (Dry Run)

Test what Terraform will create without actually deploying:

```bash
cd infrastructure/environments/dev

# Initialize (if not done)
terraform init

# Review plan
terraform plan -var-file=terraform.tfvars
```

Review the output to ensure:
- [ ] Correct number of resources
- [ ] Resource names are correct
- [ ] No errors or warnings
- [ ] Estimated costs are acceptable

## Post-Deployment Testing

### 1. Test Infrastructure

After `terraform apply`, verify resources were created:

```bash
cd infrastructure/environments/dev

# Get outputs
terraform output

# Test API Gateway
API_URL=$(terraform output -raw api_gateway_url)
echo "API Gateway: ${API_URL}"

# Test Lambda functions exist
aws lambda list-functions --query "Functions[?contains(FunctionName, 'llm-duel-arena')].FunctionName"
```

### 2. Test Lambda Functions

Test each Lambda function individually:

```bash
# Test game handler
aws lambda invoke \
  --function-name llm-duel-arena-game-dev \
  --payload '{"httpMethod":"GET","path":"/api/games/health"}' \
  response.json
cat response.json

# Test auth handler
aws lambda invoke \
  --function-name llm-duel-arena-auth-dev \
  --payload '{"httpMethod":"GET","path":"/auth/login"}' \
  response.json
cat response.json
```

### 3. Test API Gateway Endpoints

```bash
API_URL=$(cd infrastructure/environments/dev && terraform output -raw api_gateway_url)

# Test health endpoint (if exists)
curl ${API_URL}/api/games/health

# Test game creation
curl -X POST ${API_URL}/api/games/create \
  -H "Content-Type: application/json" \
  -d '{
    "game_type": "chess",
    "white_model": "ollama:llama3.1:latest",
    "black_model": "ollama:mistral-nemo:latest"
  }'
```

### 4. Test Frontend

1. **Get CloudFront URL:**
   ```bash
   cd infrastructure/environments/dev
   CLOUDFRONT_URL=$(terraform output -raw cloudfront_url)
   echo "Visit: https://${CLOUDFRONT_URL}"
   ```

2. **Test in browser:**
   - [ ] Landing page loads
   - [ ] Static assets load (CSS, JS, images)
   - [ ] API calls work (check browser console)
   - [ ] Game creation works
   - [ ] Authentication works
   - [ ] No CORS errors

3. **Check browser console:**
   - Open DevTools (F12)
   - Check for errors
   - Verify API calls are going to correct endpoints
   - Check network tab for failed requests

### 5. Test DynamoDB

```bash
# List tables
aws dynamodb list-tables

# Check game table
TABLE_NAME=$(cd infrastructure/environments/dev && terraform output -raw dynamodb_table_name)
aws dynamodb describe-table --table-name ${TABLE_NAME}

# Scan for items (if any)
aws dynamodb scan --table-name ${TABLE_NAME} --limit 5
```

### 6. Test CloudWatch Logs

```bash
# View Lambda logs
aws logs tail /aws/lambda/llm-duel-arena-game-dev --follow

# View API Gateway logs
aws logs tail /aws/apigateway/llm-duel-arena-api-dev --follow
```

## Integration Testing

### Test Full Game Flow

1. **Create a game:**
   ```bash
   curl -X POST ${API_URL}/api/games/create \
     -H "Content-Type: application/json" \
     -d '{
       "game_type": "chess",
       "white_model": "ollama:llama3.1:latest",
       "black_model": "ollama:mistral-nemo:latest"
     }'
   ```

2. **Get game state:**
   ```bash
   GAME_ID="<from-create-response>"
   curl ${API_URL}/api/games/${GAME_ID}
   ```

3. **Make a move:**
   ```bash
   curl -X POST ${API_URL}/api/games/${GAME_ID}/move \
     -H "Content-Type: application/json" \
     -d '{"move": "e2e4"}'
   ```

4. **Start autoplay:**
   ```bash
   curl -X POST ${API_URL}/api/games/${GAME_ID}/autoplay
   ```

5. **Check game state periodically:**
   ```bash
   curl ${API_URL}/api/games/${GAME_ID}
   ```

### Test Authentication Flow

1. **Initiate login:**
   ```bash
   curl ${API_URL}/auth/login
   # Should redirect to Google OAuth
   ```

2. **Test callback (after OAuth):**
   ```bash
   # This requires actual OAuth flow in browser
   ```

3. **Test user info:**
   ```bash
   curl ${API_URL}/auth/user \
     -H "Cookie: session=<session-cookie>"
   ```

## Load Testing

### Simple Load Test

```bash
# Install Apache Bench (if not installed)
# macOS: brew install httpd
# Linux: apt-get install apache2-utils

API_URL=$(cd infrastructure/environments/dev && terraform output -raw api_gateway_url)

# Test 100 requests, 10 concurrent
ab -n 100 -c 10 ${API_URL}/api/games/health
```

### Monitor During Load Test

```bash
# Watch Lambda metrics
watch -n 1 'aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=llm-duel-arena-game-dev \
  --start-time $(date -u -d "5 minutes ago" +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60 \
  --statistics Sum'
```

## Troubleshooting Tests

### Lambda Function Errors

```bash
# Get recent errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/llm-duel-arena-game-dev \
  --filter-pattern "ERROR" \
  --max-items 10
```

### API Gateway Errors

```bash
# Check API Gateway logs
aws logs tail /aws/apigateway/llm-duel-arena-api-dev --follow
```

### DynamoDB Errors

```bash
# Check table metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/DynamoDB \
  --metric-name UserErrors \
  --dimensions Name=TableName,Value=llm-duel-arena-games-dev \
  --start-time $(date -u -d "1 hour ago" +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum
```

## Test Checklist

### Pre-Deployment
- [ ] Local application works
- [ ] Deployment configuration valid
- [ ] Terraform plan shows expected resources
- [ ] No configuration errors

### Post-Deployment
- [ ] All resources created successfully
- [ ] Lambda functions exist and are configured
- [ ] API Gateway endpoints respond
- [ ] DynamoDB tables created
- [ ] S3 bucket exists and accessible
- [ ] CloudFront distribution active
- [ ] Frontend loads correctly
- [ ] API calls work from frontend
- [ ] Authentication works
- [ ] Game creation works
- [ ] Game moves work
- [ ] Logs are being written

### Production Readiness
- [ ] CloudWatch alarms configured
- [ ] Error rates acceptable
- [ ] Response times acceptable
- [ ] Cost monitoring set up
- [ ] Backup strategy in place

---

**Next Steps**: After testing, proceed with production deployment or iterate on fixes.







