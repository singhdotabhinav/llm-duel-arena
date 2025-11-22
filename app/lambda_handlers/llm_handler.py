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




