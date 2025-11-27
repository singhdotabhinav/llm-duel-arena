"""
Lambda handler for authentication service
Handles Google OAuth login, callback, and user management
"""
import json
import os
import secrets
import boto3
from typing import Dict, Any
from urllib.parse import urlencode

# Initialize services
from services.dynamodb_service import save_user, get_user_by_email

# Secrets Manager for OAuth credentials
secrets_client = boto3.client('secretsmanager', region_name=os.getenv('AWS_REGION', 'us-east-1'))


def get_oauth_credentials() -> Dict[str, str]:
    """Get OAuth credentials from Secrets Manager"""
    try:
        secret_arn = os.environ.get('GOOGLE_CLIENT_ID_SECRET_ARN')
        if not secret_arn:
            return {}
        
        response = secrets_client.get_secret_value(SecretId=secret_arn)
        secret = json.loads(response['SecretString'])
        return {
            'client_id': secret.get('client_id', ''),
            'client_secret': secret.get('client_secret', '')
        }
    except Exception as e:
        print(f"Error getting OAuth credentials: {e}")
        return {}


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle API Gateway requests for auth endpoints
    """
    http_method = event.get('requestContext', {}).get('http', {}).get('method', 'GET')
    path = event.get('rawPath', '')
    query_params = event.get('queryStringParameters') or {}
    headers = event.get('headers', {})
    
    # Route handling
    if path == '/api/auth/login':
        return handle_login(query_params)
    elif path == '/api/auth/callback':
        return handle_callback(query_params)
    elif path == '/api/auth/logout':
        return handle_logout(headers)
    elif path == '/api/auth/user':
        return get_user_info(headers)
    
    return {
        'statusCode': 404,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({'error': 'Not found'})
    }


def handle_login(query_params: Dict[str, Any]) -> Dict[str, Any]:
    """Initiate Google OAuth login"""
    credentials = get_oauth_credentials()
    if not credentials.get('client_id'):
        return error_response('Google OAuth not configured', 500)
    
    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)
    
    # Build Google OAuth URL
    redirect_uri = os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:8000/auth/callback')
    params = {
        'client_id': credentials['client_id'],
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': 'openid email profile',
        'state': state,
        'access_type': 'offline',
        'prompt': 'consent'
    }
    
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    
    # Store state in DynamoDB or return it to client (client stores in localStorage)
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'auth_url': auth_url,
            'state': state  # Client should verify this on callback
        })
    }


def handle_callback(query_params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle Google OAuth callback"""
    code = query_params.get('code')
    state = query_params.get('state')
    error = query_params.get('error')
    
    if error:
        return error_response(f'OAuth error: {error}', 400)
    
    if not code:
        return error_response('Missing authorization code', 400)
    
    # Exchange code for token (simplified - in production, do this server-side)
    # For Lambda, we'll return the code to the client to exchange
    # Or use a separate Lambda to exchange the token
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'code': code,
            'state': state,
            'message': 'Callback received. Exchange code for token on client side.'
        })
    }


def handle_logout(headers: Dict[str, Any]) -> Dict[str, Any]:
    """Handle user logout"""
    # In serverless, we can't set cookies easily
    # Client should clear localStorage/sessionStorage
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({'message': 'Logged out'})
    }


def get_user_info(headers: Dict[str, Any]) -> Dict[str, Any]:
    """Get current user info"""
    # Extract user ID from Authorization header or JWT token
    # For now, return not logged in
    # In production, decode JWT token from Authorization header
    
    auth_header = headers.get('authorization') or headers.get('Authorization', '')
    
    if not auth_header:
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'logged_in': False})
        }
    
    # TODO: Decode JWT and get user info
    # For now, return placeholder
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'logged_in': True,
            'user': {
                'id': 'user_id_from_token',
                'email': 'user@example.com'
            }
        })
    }


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







