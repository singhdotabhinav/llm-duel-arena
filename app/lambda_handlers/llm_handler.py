"""
Lambda handler for LLM service
Handles LLM API calls (OpenAI, Anthropic, Ollama)
"""
import json
import os
import boto3
from typing import Dict, Any, Optional, Tuple

# Secrets Manager for API keys
secrets_client = boto3.client('secretsmanager', region_name=os.getenv('AWS_REGION', 'us-east-1'))


def get_openai_api_key() -> Optional[str]:
    """Get OpenAI API key from Secrets Manager"""
    try:
        secret_arn = os.environ.get('OPENAI_API_KEY_SECRET_ARN')
        if not secret_arn:
            return None
        
        response = secrets_client.get_secret_value(SecretId=secret_arn)
        secret = json.loads(response['SecretString'])
        return secret.get('api_key')
    except Exception as e:
        print(f"Error getting OpenAI API key: {e}")
        return None


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle LLM API requests
    This is an internal service - should be called by game service, not directly
    """
    http_method = event.get('requestContext', {}).get('http', {}).get('method', 'POST')
    body = event.get('body', '{}')
    
    try:
        if isinstance(body, str):
            body = json.loads(body)
    except:
        body = {}
    
    if http_method != 'POST':
        return error_response('Method not allowed', 405)
    
    # Extract request parameters
    model_name = body.get('model_name', '')
    prompt = body.get('prompt', '')
    game_type = body.get('game_type', 'chess')
    engine_state = body.get('engine_state', '')
    
    if not model_name or not prompt:
        return error_response('model_name and prompt required', 400)
    
    # Call LLM adapter
    move, error = call_llm(model_name, prompt, game_type, engine_state)
    
    if error:
        return error_response(error, 500)
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'move': move,
            'tokens_used': 0  # TODO: Track tokens
        })
    }


def call_llm(model_name: str, prompt: str, game_type: str, engine_state: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Call appropriate LLM based on model name
    Returns: (move, error)
    """
    try:
        # Determine adapter type
        if model_name.startswith('openai:'):
            return call_openai(model_name.replace('openai:', ''), prompt)
        elif model_name.startswith('anthropic:'):
            return call_anthropic(model_name.replace('anthropic:', ''), prompt)
        elif model_name.startswith('ollama:'):
            return call_ollama(model_name.replace('ollama:', ''), prompt, game_type, engine_state)
        elif model_name.startswith('hf:'):
            return call_huggingface(model_name, prompt, game_type)
        else:
            return None, f"Unknown model type: {model_name}"
    except Exception as e:
        return None, str(e)


def call_openai(model: str, prompt: str) -> Tuple[Optional[str], Optional[str]]:
    """Call OpenAI API"""
    api_key = get_openai_api_key()
    if not api_key:
        return None, "OpenAI API key not configured"
    
    try:
        import httpx
        
        response = httpx.post(
            'https://api.openai.com/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            },
            json={
                'model': model,
                'messages': [
                    {'role': 'system', 'content': 'You are a game-playing AI.'},
                    {'role': 'user', 'content': prompt}
                ],
                'temperature': 0.4,
                'max_tokens': 10
            },
            timeout=30.0
        )
        
        if response.status_code != 200:
            return None, f"OpenAI API error: {response.text}"
        
        data = response.json()
        move = data['choices'][0]['message']['content'].strip()
        return move, None
    except Exception as e:
        return None, f"OpenAI API call failed: {e}"


def call_anthropic(model: str, prompt: str) -> Tuple[Optional[str], Optional[str]]:
    """Call Anthropic API"""
    # Similar to OpenAI, but using Anthropic SDK
    return None, "Anthropic adapter not yet implemented"


def call_ollama(model: str, prompt: str, game_type: str, engine_state: str) -> Tuple[Optional[str], Optional[str]]:
    """Call Ollama API (local or remote)"""
    try:
        import httpx
        
        ollama_url = os.getenv('OLLAMA_URL', 'http://localhost:11434')
        
        response = httpx.post(
            f'{ollama_url}/api/generate',
            json={
                'model': model,
                'prompt': prompt,
                'stream': False,
                'options': {
                    'temperature': 0.4,
                    'num_predict': 10
                }
            },
            timeout=30.0
        )
        
        if response.status_code != 200:
            return None, f"Ollama API error: {response.text}"
        
        data = response.json()
        move = data.get('response', '').strip()
        return move, None
    except Exception as e:
        return None, f"Ollama API call failed: {e}"


def call_huggingface(model_name: str, prompt: str, game_type: str) -> Tuple[Optional[str], Optional[str]]:
    """Call HuggingFace Inference API (FREE tier: 30K requests/month)"""
    try:
        import httpx
        
        # Parse model name
        if model_name.startswith('hf:'):
            hf_model = model_name.replace('hf:', '')
        else:
            hf_model = model_name
        
        # Default to TinyLlama if not specified
        if not hf_model or hf_model == 'hf':
            hf_model = 'TinyLlama/TinyLlama-1.1B-Chat-v1.0'
        
        # Get API token from Secrets Manager or environment
        api_token = os.getenv('HUGGINGFACE_API_TOKEN', '')
        if not api_token:
            # Try to get from Secrets Manager
            try:
                secret_arn = os.environ.get('HUGGINGFACE_API_TOKEN_SECRET_ARN')
                if secret_arn:
                    response = secrets_client.get_secret_value(SecretId=secret_arn)
                    secret = json.loads(response['SecretString'])
                    api_token = secret.get('api_token', '')
            except Exception:
                pass
        
        base_url = f"https://api-inference.huggingface.co/models/{hf_model}"
        
        headers = {"Content-Type": "application/json"}
        if api_token:
            headers["Authorization"] = f"Bearer {api_token}"
        
        # Determine max tokens based on game type
        max_tokens_map = {
            'chess': 8,
            'tic_tac_toe': 5,
            'rock_paper_scissors': 3,
            'racing': 4,
            'word_association_clash': 6
        }
        max_tokens = max_tokens_map.get(game_type, 10)
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": max_tokens,
                "temperature": 0.4,
                "return_full_text": False
            }
        }
        
        response = httpx.post(
            base_url,
            json=payload,
            headers=headers,
            timeout=30.0
        )
        
        # Handle rate limiting / model loading
        if response.status_code == 503:
            import time
            time.sleep(5)  # Wait for model to load
            response = httpx.post(base_url, json=payload, headers=headers, timeout=30.0)
        
        if response.status_code != 200:
            if response.status_code == 429:
                return None, "HuggingFace API rate limit exceeded. Free tier: 30K requests/month."
            return None, f"HuggingFace API error {response.status_code}: {response.text}"
        
        data = response.json()
        
        # HuggingFace returns different formats
        if isinstance(data, list) and len(data) > 0:
            move = data[0].get('generated_text', '').strip()
        elif isinstance(data, dict):
            move = data.get('generated_text', '').strip()
        else:
            move = str(data).strip()
        
        return move, None
    except Exception as e:
        return None, f"HuggingFace API call failed: {e}"


def error_response(message: str, status_code: int = 400) -> Dict[str, Any]:
    """Return error response"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({'error': message})
    }




