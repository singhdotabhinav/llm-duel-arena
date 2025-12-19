"""
Lambda handler for game service
Converts FastAPI routes to Lambda functions
"""

import json
import os
import time
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Import your existing game logic
import sys

sys.path.append("/opt/python")  # For Lambda layers

from services.game_manager import game_manager
from services.match_runner import match_runner
from services.dynamodb_service import save_game_to_db, get_game_from_db, get_user_games


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle API Gateway requests for game endpoints
    """
    http_method = event.get("requestContext", {}).get("http", {}).get("method", "GET")
    path = event.get("rawPath", "")
    path_params = event.get("pathParameters") or {}
    query_params = event.get("queryStringParameters") or {}
    body = event.get("body", "{}")

    try:
        if isinstance(body, str):
            body = json.loads(body)
    except:
        body = {}

    # Route handling - API Gateway v2 format
    if path.startswith("/api/games"):
        game_id = (
            path_params.get("game_id") or path_params.get("proxy", "").split("/")[0] if path_params.get("proxy") else None
        )

        if http_method == "POST" and path == "/api/games":
            return create_game(body, query_params)
        elif http_method == "GET" and game_id:
            if path.endswith("/start_autoplay") or "start_autoplay" in path:
                return error_response("Use POST method for start_autoplay", 405)
            return get_game(game_id)
        elif http_method == "POST" and game_id and "move" in path:
            return make_move(game_id, body)
        elif http_method == "POST" and game_id and "start_autoplay" in path:
            return start_autoplay(game_id, body)
        elif http_method == "GET" and path == "/api/games/list":
            return list_games(query_params)
        elif http_method == "GET" and path == "/api/games/my-games":
            return get_my_games(query_params)

    return {
        "statusCode": 404,
        "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
        "body": json.dumps({"error": "Not found"}),
    }


def create_game(body: Dict, query_params: Dict) -> Dict[str, Any]:
    """Create a new game"""
    try:
        game_type = body.get("game_type", "chess")
        white_model = body.get("white_model")
        black_model = body.get("black_model")
        user_id = query_params.get("user_id")  # Get from query or JWT token

        state = game_manager.create_game(game_type, white_model, black_model)

        # Save to DynamoDB
        save_game_to_db(state, user_id)

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": json.dumps(
                {
                    "game_id": state.game_id,
                    "game_type": state.game_type,
                    "state": state.state,
                    "turn": state.turn,
                    "over": state.over,
                }
            ),
        }
    except Exception as e:
        logger.debug(f"Error creating game: {e}")
        return error_response(str(e))


def get_game(game_id: str) -> Dict[str, Any]:
    """Get game state"""
    try:
        state = game_manager.get_state(game_id)
        if not state:
            return {
                "statusCode": 404,
                "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
                "body": json.dumps({"error": "Game not found"}),
            }

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": json.dumps(
                {
                    "game_id": state.game_id,
                    "game_type": state.game_type,
                    "state": state.state,
                    "turn": state.turn,
                    "over": state.over,
                    "result": state.result,
                }
            ),
        }
    except Exception as e:
        return error_response(str(e))


def make_move(game_id: str, body: Dict) -> Dict[str, Any]:
    """Make a move"""
    try:
        move = body.get("move")
        if not move:
            return error_response("Move required")

        updated = game_manager.push_move(game_id, move, model_name="manual")

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": json.dumps(
                {"game_id": updated.game_id, "state": updated.state, "turn": updated.turn, "over": updated.over}
            ),
        }
    except Exception as e:
        return error_response(str(e))


def start_autoplay(game_id: str, body: Dict) -> Dict[str, Any]:
    """Start autoplay"""
    try:
        white_model = body.get("white_model")
        black_model = body.get("black_model")

        match_runner.start(game_id, white_model, black_model)

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"status": "started"}),
        }
    except Exception as e:
        return error_response(str(e))


def list_games(query_params: Dict) -> Dict[str, Any]:
    """List all games (public games)"""
    try:
        # For now, return empty list
        # In production, implement pagination and filtering
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"games": []}),
        }
    except Exception as e:
        return error_response(str(e))


def get_my_games(query_params: Dict) -> Dict[str, Any]:
    """Get games for logged-in user"""
    try:
        user_id = query_params.get("user_id")
        if not user_id:
            return error_response("User ID required", 401)

        games = get_user_games(user_id, limit=100)

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"games": games}),
        }
    except Exception as e:
        return error_response(str(e))


def error_response(message: str) -> Dict[str, Any]:
    """Return error response"""
    return {
        "statusCode": 500,
        "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
        "body": json.dumps({"error": message}),
    }
