# 🚀 Quick Deploy Guide - Zero Cost

## TL;DR - Get Live in 30 Minutes

### Step 1: Get Free HuggingFace API (5 min)
```bash
# 1. Sign up: https://huggingface.co/join
# 2. Get token: https://huggingface.co/settings/tokens
# 3. Test it:
export HUGGINGFACE_API_TOKEN="hf_..."
curl https://api-inference.huggingface.co/models/TinyLlama/TinyLlama-1.1B-Chat-v1.0 \
  -H "Authorization: Bearer $HUGGINGFACE_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"inputs": "Hello"}'
```

### Step 2: Set Up AWS (10 min)
```bash
# 1. Create AWS account: https://aws.amazon.com/free/
# 2. Install AWS CLI: brew install awscli
# 3. Configure: aws configure
# 4. Store HuggingFace token:
aws secretsmanager create-secret \
  --name llm-duel-arena-hf-token-dev \
  --secret-string "{\"api_token\":\"$HUGGINGFACE_API_TOKEN\"}"
```

### Step 3: Deploy (15 min)
```bash
cd infrastructure/environments/dev
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your project name

terraform init
terraform apply  # Type 'yes'

cd ../..
./build-lambda.sh dev
./deploy.sh dev us-east-1
./deploy-static.sh dev us-east-1
```

### Step 4: Get Your URL
```bash
terraform output cloudfront_url
# Visit that URL - you're live! 🎉
```

---

## 💰 Cost: $0/month

- ✅ AWS Free Tier: Lambda, API Gateway, DynamoDB, S3, CloudFront
- ✅ HuggingFace Free: 30,000 requests/month
- ✅ Total: **$0**

---

## 🎮 Use Free Models

Update your Lambda environment variables:
```bash
DEFAULT_WHITE_MODEL=hf:TinyLlama/TinyLlama-1.1B-Chat-v1.0
DEFAULT_BLACK_MODEL=hf:microsoft/Phi-2
```

Available free models:
- `hf:TinyLlama/TinyLlama-1.1B-Chat-v1.0` - Fastest ⚡
- `hf:microsoft/Phi-2` - Best quality 🏆
- `hf:gpt2` - Ultra-lightweight 🪶

---

## 📚 Full Guide

See `FREE_HOSTING_GUIDE.md` for complete step-by-step instructions.

---

## ⚠️ Important Notes

1. **Ollama won't work on Lambda** - Use HuggingFace API instead
2. **Set billing alerts** - Monitor costs (should be $0)
3. **Free tier limits**:
   - HuggingFace: 30K requests/month (~1,000 games)
   - AWS: 1M Lambda requests/month (plenty)

---

## 🆘 Troubleshooting

**Rate limit errors?**
- You've hit 30K/month limit
- Wait until next month OR upgrade HuggingFace ($0.0001/request)

**Lambda timeout?**
- Increase timeout to 60s in `lambda.tf`
- Use faster models (TinyLlama)

**Costs appearing?**
- Check you're using free tier services
- Verify no EC2 instances running
- Review Cost Explorer

---

**You're all set! 🎉**

