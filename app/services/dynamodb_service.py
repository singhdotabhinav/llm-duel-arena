"""
DynamoDB service layer to replace SQLAlchemy
Single-table design for cost optimization
"""
import json
import boto3
import os
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb', region_name=os.getenv('AWS_REGION', 'us-east-1'))
table_name = os.getenv('DYNAMODB_TABLE', 'llm-duel-arena-games-dev')

# Get table reference
try:
    games_table = dynamodb.Table(table_name)
except:
    games_table = None  # Will be set during initialization


def get_table():
    """Get DynamoDB table (lazy initialization)"""
    global games_table
    if games_table is None:
        table_name = os.getenv('DYNAMODB_TABLE', 'llm-duel-arena-games-dev')
        games_table = dynamodb.Table(table_name)
    return games_table


def save_game_to_db(game_state: Any, user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Save or update a game in DynamoDB
    Uses single-table design: PK=game_id, SK=move_id or 'metadata'
    """
    table = get_table()
    
    # Prepare game state
    state_json = {
        "state": game_state.state,
        "moves": [
            {
                "ply": m.ply,
                "side": m.side,
                "move_uci": m.move_uci,
                "move_san": m.move_san,
                "model_name": m.model_name,
                "error": m.error,
                "tokens_used": getattr(m, 'tokens_used', 0)
            }
            for m in game_state.moves
        ]
    }
    
    # Save game metadata
    now = datetime.utcnow().isoformat()
    item = {
        'game_id': game_state.game_id,
        'move_id': 'metadata',  # Use 'metadata' as SK for game info
        'user_id': user_id or 'anonymous',
        'game_type': game_state.game_type,
        'white_model': game_state.white_model or '',
        'black_model': game_state.black_model or '',
        'result': game_state.result.get("result", ""),
        'winner': game_state.result.get("winner"),
        'moves_count': len(game_state.moves),
        'is_over': 1 if game_state.over else 0,
        'white_tokens': getattr(game_state, 'white_tokens', 0),
        'black_tokens': getattr(game_state, 'black_tokens', 0),
        'game_state': json.dumps(state_json),
        'created_at': now,
        'updated_at': now,
        'ttl': int(datetime.utcnow().timestamp()) + (30 * 24 * 60 * 60)  # 30 days
    }
    
    # Convert to DynamoDB format (handle Decimal)
    item = json.loads(json.dumps(item), parse_float=Decimal)
    
    table.put_item(Item=item)
    
    # Save individual moves (optional, for querying moves separately)
    for move in game_state.moves:
        move_item = {
            'game_id': game_state.game_id,
            'move_id': f"move_{move.ply:04d}",  # Zero-padded for sorting
            'ply': move.ply,
            'side': move.side,
            'move_uci': move.move_uci,
            'move_san': move.move_san or '',
            'model_name': move.model_name or '',
            'error': move.error or '',
            'tokens_used': getattr(move, 'tokens_used', 0),
            'created_at': now,
            'ttl': int(datetime.utcnow().timestamp()) + (30 * 24 * 60 * 60)
        }
        move_item = json.loads(json.dumps(move_item), parse_float=Decimal)
        table.put_item(Item=move_item)
    
    return item


def get_user_games(user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
    """Get all games for a user using GSI"""
    table = get_table()
    
    try:
        response = table.query(
            IndexName='user-games-index',
            KeyConditionExpression='user_id = :uid AND move_id = :metadata',
            ExpressionAttributeValues={
                ':uid': user_id,
                ':metadata': 'metadata'
            },
            ScanIndexForward=False,  # Most recent first
            Limit=limit
        )
        
        games = []
        for item in response.get('Items', []):
            # Convert Decimal to int/float
            game = {k: int(v) if isinstance(v, Decimal) and v % 1 == 0 else float(v) if isinstance(v, Decimal) else v 
                   for k, v in item.items()}
            games.append(game)
        
        return games
    except Exception as e:
        print(f"Error querying user games: {e}")
        return []


def get_game_from_db(game_id: str) -> Optional[Dict[str, Any]]:
    """Get a single game by ID"""
    table = get_table()
    
    try:
        response = table.get_item(
            Key={
                'game_id': game_id,
                'move_id': 'metadata'
            }
        )
        
        if 'Item' not in response:
            return None
        
        item = response['Item']
        # Convert Decimal to int/float
        game = {k: int(v) if isinstance(v, Decimal) and v % 1 == 0 else float(v) if isinstance(v, Decimal) else v 
               for k, v in item.items()}
        return game
    except Exception as e:
        print(f"Error getting game: {e}")
        return None


def get_game_moves(game_id: str) -> List[Dict[str, Any]]:
    """Get all moves for a game"""
    table = get_table()
    
    try:
        response = table.query(
            KeyConditionExpression='game_id = :gid AND begins_with(move_id, :prefix)',
            ExpressionAttributeValues={
                ':gid': game_id,
                ':prefix': 'move_'
            },
            ScanIndexForward=True  # Oldest first
        )
        
        moves = []
        for item in response.get('Items', []):
            move = {k: int(v) if isinstance(v, Decimal) and v % 1 == 0 else float(v) if isinstance(v, Decimal) else v 
                   for k, v in item.items()}
            moves.append(move)
        
        return sorted(moves, key=lambda x: x.get('ply', 0))
    except Exception as e:
        print(f"Error getting game moves: {e}")
        return []


def save_user(user_id: str, email: str, name: Optional[str] = None, picture: Optional[str] = None) -> Dict[str, Any]:
    """Save or update a user"""
    table = get_table()
    
    now = datetime.utcnow().isoformat()
    item = {
        'game_id': f"user_{user_id}",  # Use user_id as PK
        'move_id': 'metadata',  # Use 'metadata' as SK
        'user_id': user_id,
        'email': email,
        'name': name or '',
        'picture': picture or '',
        'created_at': now,
        'last_login': now,
        'ttl': int(datetime.utcnow().timestamp()) + (365 * 24 * 60 * 60)  # 1 year
    }
    
    item = json.loads(json.dumps(item), parse_float=Decimal)
    table.put_item(Item=item)
    
    return item


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get user by email using GSI"""
    table = get_table()
    
    try:
        # Note: This requires an email-index GSI
        # For now, we'll scan (not efficient, but works for small datasets)
        response = table.scan(
            FilterExpression='email = :email AND move_id = :metadata',
            ExpressionAttributeValues={
                ':email': email,
                ':metadata': 'metadata'
            },
            Limit=1
        )
        
        if response.get('Items'):
            item = response['Items'][0]
            user = {k: int(v) if isinstance(v, Decimal) and v % 1 == 0 else float(v) if isinstance(v, Decimal) else v 
                   for k, v in item.items()}
            return user
        
        return None
    except Exception as e:
        print(f"Error getting user by email: {e}")
        return None

