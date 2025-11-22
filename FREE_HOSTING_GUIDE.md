# 🆓 Free Hosting Guide - LLM Duel Arena

Complete step-by-step guide to host your website for **FREE** using AWS Free Tier + HuggingFace Free Inference API.

## 📊 Cost Breakdown (All FREE)

| Service | Free Tier | Your Usage | Cost |
|---------|-----------|------------|------|
| **AWS Lambda** | 1M requests/month | ~500-1000 games/month | ✅ $0 |
| **API Gateway** | 1M requests/month | ~500-1000 games/month | ✅ $0 |
| **DynamoDB** | 25 GB storage, 25 RCU/WCU | Small app | ✅ $0 |
| **S3** | 5 GB storage | Static files | ✅ $0 |
| **CloudFront** | 50 GB transfer/month | Low traffic | ✅ $0 |
| **HuggingFace API** | 30,000 requests/month | ~500-1000 games | ✅ $0 |
| **Domain** | Cloudflare (free) | DNS only | ✅ $0 |

**Total Monthly Cost: $0** 🎉

---

## 🎯 Strategy: Why This Works

### ❌ Problem with Local Models (Ollama)
- **Lambda can't run Ollama**: No GPU, 512MB-10GB limit, 15min timeout
- **EC2 with GPU**: Costs $0.50-5/hour (not free)
- **Local models too heavy**: Even TinyLlama needs GPU

### ✅ Solution: HuggingFace Inference API (FREE)
- **Free tier**: 30,000 requests/month
- **No infrastructure needed**: They host the models
- **Lightweight models**: TinyLlama, Phi-2, GPT-2 (all free)
- **Fast**: API calls are quick, no model loading

---

## 🚀 Step-by-Step Deployment

### Phase 1: Get Free Domain (Optional but Recommended)

#### Option A: Free Subdomain (Easiest)
- Use Cloudflare Pages: `yourname.pages.dev` (completely free)
- Or use AWS Amplify: `yourname.amplifyapp.com` (free)

#### Option B: Free Domain (Limited)
1. Go to [Freenom](https://www.freenom.com) (free .tk, .ml, .ga domains)
2. Register a free domain (e.g., `llmduel.tk`)
3. Point DNS to Cloudflare (free DNS)

#### Option C: Buy Cheap Domain ($1-2/year)
- Namecheap: `.xyz` domains for $1/year
- Google Domains: Various cheap options

**Recommendation**: Start with Cloudflare Pages subdomain (free), upgrade later if needed.

---

### Phase 2: Set Up HuggingFace Free API

1. **Create HuggingFace Account**
   ```bash
   # Go to: https://huggingface.co/join
   # Sign up for free account
   ```

2. **Get Free API Token**
   - Go to: https://huggingface.co/settings/tokens
   - Create new token (read access is enough)
   - Copy token (starts with `hf_...`)

3. **Test Free API**
   ```bash
   curl https://api-inference.huggingface.co/models/TinyLlama/TinyLlama-1.1B-Chat-v1.0 \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"inputs": "Hello"}'
   ```

**Free Models Available** (all work great for games):
- `TinyLlama/TinyLlama-1.1B-Chat-v1.0` - 1.1B params, very fast
- `microsoft/Phi-2` - 2.7B params, good quality
- `gpt2` - 124M params, ultra-lightweight
- `google/flan-t5-small` - 60M params, fastest

**Free Tier Limits**:
- 30,000 requests/month
- Rate limit: ~30 requests/minute
- Perfect for your use case!

---

### Phase 3: Create HuggingFace Adapter

Create a new adapter for HuggingFace Inference API:

```python
# app/models/huggingface_adapter.py
from __future__ import annotations
import json
import re
from typing import Optional, Tuple
import httpx
import os
from ..services.chess_engine import ChessEngine
from .base import ModelAdapter

UCI_REGEX = re.compile(r"\b([a-h][1-8][a-h][1-8][qrbn]?)\b", re.IGNORECASE)
RPS_REGEX = re.compile(r"\b(rock|paper|scissors|r|p|s)\b", re.IGNORECASE)

class HuggingFaceAdapter(ModelAdapter):
    def __init__(self, model_name: str) -> None:
        super().__init__(model_name)
        # Default to TinyLlama if not specified
        self.hf_model = model_name.replace('hf:', '') if model_name.startswith('hf:') else 'TinyLlama/TinyLlama-1.1B-Chat-v1.0'
        self.api_token = os.getenv('HUGGINGFACE_API_TOKEN', '')
        self.base_url = f"https://api-inference.huggingface.co/models/{self.hf_model}"
    
    async def get_move(self, engine) -> Tuple[Optional[str], Optional[str]]:
        # Detect game type
        is_chess = hasattr(engine, 'board') and hasattr(engine.board, 'legal_moves')
        is_rps = hasattr(engine, 'white_choice') and hasattr(engine, 'black_choice')
        is_racing = hasattr(engine, 'white_position') and hasattr(engine, 'black_position')
        
        if is_chess:
            legal = engine.legal_moves()
            if not legal:
                return None, "no legal moves"
            prompt = f"Chess FEN: {engine.get_state()}. Return ONLY one UCI move like 'e2e4'."
            max_tokens = 8
        elif is_rps:
            legal = engine.legal_moves()
            if not legal:
                return None, "no legal moves"
            prompt = "Rock Paper Scissors. Choose: rock, paper, or scissors. Return ONLY the choice."
            max_tokens = 3
        elif is_racing:
            legal = engine.legal_moves()
            if not legal:
                return None, "no legal moves"
            prompt = f"Racing game. Position: {engine.white_position if engine.get_turn() == 'white' else engine.black_position}/100. Choose: accelerate, boost, or maintain. Return ONLY the action."
            max_tokens = 4
        else:
            return None, "unknown game type"
        
        try:
            headers = {"Content-Type": "application/json"}
            if self.api_token:
                headers["Authorization"] = f"Bearer {self.api_token}"
            
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": max_tokens,
                    "temperature": 0.4,
                    "return_full_text": False
                }
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(self.base_url, json=payload, headers=headers)
                resp.raise_for_status()
                
                data = resp.json()
                
                # HuggingFace returns different formats
                if isinstance(data, list) and len(data) > 0:
                    content = data[0].get('generated_text', '')
                elif isinstance(data, dict):
                    content = data.get('generated_text', '')
                else:
                    content = str(data)
                
                content = content.strip()
                
                # Track tokens (estimate)
                self.tokens_used += len(content.split()) * 1.3  # Rough estimate
                
                # Extract move
                if is_chess:
                    move = self._extract_uci(content)
                    if move in legal:
                        return move, None
                elif is_rps:
                    move = self._extract_rps(content)
                    if move in legal:
                        return move, None
                elif is_racing:
                    move = self._extract_racing(content)
                    if move in legal:
                        return move, None
                
                return None, f"illegal or unparsed move: {content}"
        except Exception as e:
            return None, str(e)
    
    def _extract_uci(self, text: str) -> Optional[str]:
        m = UCI_REGEX.search(text)
        if m:
            return m.group(1).lower()
        return None
    
    def _extract_rps(self, text: str) -> Optional[str]:
        m = RPS_REGEX.search(text.lower())
        if m:
            choice = m.group(1).lower()
            if choice == 'r':
                return 'rock'
            elif choice == 'p':
                return 'paper'
            elif choice == 's':
                return 'scissors'
            return choice
        return None
    
    def _extract_racing(self, text: str) -> Optional[str]:
        text = text.lower().strip()
        if 'boost' in text:
            return 'boost'
        elif 'accelerate' in text or 'accel' in text:
            return 'accelerate'
        elif 'maintain' in text:
            return 'maintain'
        return None
```

Update `llm_handler.py` to support HuggingFace:

```python
# Add to llm_handler.py imports
from models.huggingface_adapter import HuggingFaceAdapter

# In call_llm function, add:
elif model_name.startswith('hf:'):
    adapter = HuggingFaceAdapter(model_name)
    return adapter.get_move(...)  # Adapt to your interface
```

---

### Phase 4: Deploy to AWS (Free Tier)

#### Step 1: Set Up AWS Account
1. Go to https://aws.amazon.com/free/
2. Create account (requires credit card, but won't charge if you stay in free tier)
3. Enable MFA for security

#### Step 2: Configure AWS CLI
```bash
# Install AWS CLI
brew install awscli  # macOS
# or: pip install awscli

# Configure credentials
aws configure
# Enter: Access Key ID, Secret Access Key, Region (us-east-1), Output (json)
```

#### Step 3: Set Up Terraform State Backend
```bash
cd infrastructure
./setup-state-bucket.sh us-east-1
```

#### Step 4: Configure Environment Variables
```bash
cd infrastructure/environments/dev
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars`:
```hcl
project_name = "llm-duel-arena"
environment  = "dev"
region       = "us-east-1"
```

#### Step 5: Store Secrets in AWS Secrets Manager
```bash
# Store HuggingFace token
aws secretsmanager create-secret \
  --name llm-duel-arena-hf-token-dev \
  --secret-string '{"api_token":"YOUR_HF_TOKEN_HERE"}'

# Store Google OAuth (if using)
aws secretsmanager create-secret \
  --name llm-duel-arena-google-oauth-dev \
  --secret-string '{"client_id":"...","client_secret":"..."}'

# Store OpenAI key (optional, for fallback)
aws secretsmanager create-secret \
  --name llm-duel-arena-openai-key-dev \
  --secret-string '{"api_key":"sk-..."}'
```

#### Step 6: Deploy Infrastructure
```bash
cd infrastructure/environments/dev
terraform init
terraform plan
terraform apply  # Type 'yes' when prompted
```

#### Step 7: Build and Deploy Lambda Functions
```bash
cd infrastructure
./build-lambda.sh dev
./deploy.sh dev us-east-1
```

#### Step 8: Deploy Static Assets
```bash
./deploy-static.sh dev us-east-1
```

#### Step 9: Get Your URLs
```bash
# Get API Gateway URL
terraform output api_gateway_url

# Get CloudFront URL
terraform output cloudfront_url
```

---

### Phase 5: Configure Domain (Optional)

#### Using Cloudflare (Free)
1. Sign up at https://cloudflare.com (free)
2. Add your domain (or use their free subdomain)
3. Point DNS to CloudFront:
   - Type: CNAME
   - Name: @ (or www)
   - Content: `your-cloudfront-url.cloudfront.net`

#### Using AWS Route53 (Not Free)
- Costs $0.50/month per hosted zone
- Better integration with AWS
- Skip if budget is tight

---

## 💰 Cost Monitoring

### Set Up Billing Alerts
```bash
# Create SNS topic for alerts
aws sns create-topic --name billing-alerts

# Subscribe your email
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:ACCOUNT_ID:billing-alerts \
  --protocol email \
  --notification-endpoint your@email.com

# Create billing alarm (alert if > $1)
aws cloudwatch put-metric-alarm \
  --alarm-name billing-alert \
  --alarm-description "Alert if charges exceed $1" \
  --metric-name EstimatedCharges \
  --namespace AWS/Billing \
  --statistic Maximum \
  --period 86400 \
  --evaluation-periods 1 \
  --threshold 1 \
  --comparison-operator GreaterThanThreshold
```

### Monitor Usage
- AWS Cost Explorer: https://console.aws.amazon.com/cost-management/
- Set budget: $0/month (will alert if any charges)

---

## 🎮 Using Your Deployed App

### Default Models (Free)
Update your `.env` or Lambda environment variables:
```bash
DEFAULT_WHITE_MODEL=hf:TinyLlama/TinyLlama-1.1B-Chat-v1.0
DEFAULT_BLACK_MODEL=hf:microsoft/Phi-2
```

### Available Free Models
- `hf:TinyLlama/TinyLlama-1.1B-Chat-v1.0` - Fastest, good for games
- `hf:microsoft/Phi-2` - Better quality, slightly slower
- `hf:gpt2` - Ultra-lightweight, basic responses
- `hf:google/flan-t5-small` - Fastest, good for structured tasks

---

## 🔧 Troubleshooting

### HuggingFace API Rate Limits
- **Problem**: Too many requests
- **Solution**: Add retry logic with exponential backoff
- **Alternative**: Use multiple models (round-robin)

### Lambda Timeout
- **Problem**: LLM calls taking too long
- **Solution**: Increase timeout to 60s, use faster models (TinyLlama)

### Costs Appearing
- **Check**: Are you using free tier services?
- **Verify**: No EC2 instances running
- **Monitor**: Check Cost Explorer daily first week

---

## 📊 Expected Performance

### Free Tier Limits
- **HuggingFace**: 30,000 requests/month = ~1,000 games/month
- **Lambda**: 1M requests/month = plenty
- **API Gateway**: 1M requests/month = plenty
- **DynamoDB**: 25GB storage = thousands of games

### Response Times
- **TinyLlama**: ~1-2 seconds per move
- **Phi-2**: ~2-3 seconds per move
- **GPT-2**: ~0.5-1 second per move

---

## 🚀 Quick Start Commands

```bash
# 1. Set up HuggingFace
export HUGGINGFACE_API_TOKEN="hf_..."

# 2. Deploy to AWS
cd infrastructure/environments/dev
terraform init && terraform apply

# 3. Build Lambda
cd ../..
./build-lambda.sh dev
./deploy.sh dev us-east-1

# 4. Deploy static files
./deploy-static.sh dev us-east-1

# 5. Get your URL
terraform output cloudfront_url
```

---

## ✅ Checklist

- [ ] Create HuggingFace account and get API token
- [ ] Create AWS account (free tier)
- [ ] Set up AWS CLI
- [ ] Create HuggingFace adapter code
- [ ] Store secrets in AWS Secrets Manager
- [ ] Deploy infrastructure with Terraform
- [ ] Build and deploy Lambda functions
- [ ] Deploy static assets to S3
- [ ] Test your deployed app
- [ ] Set up billing alerts
- [ ] Configure domain (optional)

---

## 🎯 Recommendation

**Best Approach for Zero Cost**:
1. ✅ Use **HuggingFace Free API** (30K requests/month)
2. ✅ Use **AWS Free Tier** (Lambda, API Gateway, DynamoDB, S3, CloudFront)
3. ✅ Use **Cloudflare Pages** for free subdomain
4. ✅ Start with **TinyLlama** model (fastest, free)
5. ✅ Monitor costs daily first week

**Total Cost: $0/month** 🎉

**If you exceed free tier**:
- HuggingFace: $0.0001 per request (very cheap)
- AWS: Still very cheap (~$1-5/month for moderate traffic)

---

## 📞 Need Help?

- AWS Free Tier: https://aws.amazon.com/free/
- HuggingFace API: https://huggingface.co/docs/api-inference
- Cloudflare Pages: https://pages.cloudflare.com/

---

**You're all set! Your app will be live and completely free! 🚀**

