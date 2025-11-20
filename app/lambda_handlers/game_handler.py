"""
Lambda handler for game service
Converts FastAPI routes to Lambda functions
"""
import json
import os
import time
import boto3
from typing import Dict, Any

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb')
games_table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])

# Import your existing game logic
import sys
sys.path.append('/opt/python')  # For Lambda layers

from services.game_manager import game_manager
from services.match_runner import match_runner


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle API Gateway requests for game endpoints
    """
    http_method = event.get('requestContext', {}).get('http', {}).get('method', 'GET')
    path = event.get('rawPath', '')
    path_params = event.get('pathParameters') or {}
    query_params = event.get('queryStringParameters') or {}
    body = event.get('body', '{}')
    
    try:
        if isinstance(body, str):
            body = json.loads(body)
    except:
        body = {}
    
    # Route handling
    if path.startswith('/api/games'):
        if http_method == 'POST' and path == '/api/games':
            return create_game(body)
        elif http_method == 'GET' and path_params.get('game_id'):
            return get_game(path_params['game_id'])
        elif http_method == 'POST' and path_params.get('game_id') == 'move':
            return make_move(path_params['game_id'], body)
        elif http_method == 'POST' and path_params.get('game_id') == 'start_autoplay':
            return start_autoplay(path_params['game_id'], body)
        elif http_method == 'GET' and path == '/api/games/list':
            return list_games()
    
    return {
        'statusCode': 404,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({'error': 'Not found'})
    }


def create_game(body: Dict) -> Dict[str, Any]:
    """Create a new game"""
    try:
        game_type = body.get('game_type', 'chess')
        white_model = body.get('white_model')
        black_model = body.get('black_model')
        
        state = game_manager.create_game(game_type, white_model, black_model)
        
        # Save to DynamoDB
        games_table.put_item(Item={
            'game_id': state.game_id,
            'move_id': 'metadata',
            'game_type': state.game_type,
            'state': state.state,
            'white_model': white_model,
            'black_model': black_model,
            'created_at': str(int(time.time())),
            'ttl': int(time.time()) + (30 * 24 * 60 * 60)  # 30 days TTL
        })
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'game_id': state.game_id,
                'game_type': state.game_type,
                'state': state.state
            })
        }
    except Exception as e:
        return error_response(str(e))


def get_game(game_id: str) -> Dict[str, Any]:
    """Get game state"""
    try:
        state = game_manager.get_state(game_id)
        if not state:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Game not found'})
            }
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'game_id': state.game_id,
                'game_type': state.game_type,
                'state': state.state,
                'turn': state.turn,
                'over': state.over,
                'result': state.result
            })
        }
    except Exception as e:
        return error_response(str(e))


def make_move(game_id: str, body: Dict) -> Dict[str, Any]:
    """Make a move"""
    try:
        move = body.get('move')
        if not move:
            return error_response('Move required')
        
        updated = game_manager.push_move(game_id, move, model_name='manual')
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'game_id': updated.game_id,
                'state': updated.state,
                'turn': updated.turn,
                'over': updated.over
            })
        }
    except Exception as e:
        return error_response(str(e))


def start_autoplay(game_id: str, body: Dict) -> Dict[str, Any]:
    """Start autoplay"""
    try:
        white_model = body.get('white_model')
        black_model = body.get('black_model')
        
        match_runner.start(game_id, white_model, black_model)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'status': 'started'})
        }
    except Exception as e:
        return error_response(str(e))


def list_games() -> Dict[str, Any]:
    """List all games"""
    try:
        # Query DynamoDB
        response = games_table.query(
            IndexName='user-games-index',
            KeyConditionExpression='move_id = :metadata',
            ExpressionAttributeValues={':metadata': 'metadata'}
        )
        
        games = [item for item in response.get('Items', [])]
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'games': games})
        }
    except Exception as e:
        return error_response(str(e))


def error_response(message: str) -> Dict[str, Any]:
    """Return error response"""
    return {
        'statusCode': 500,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({'error': message})
    }

