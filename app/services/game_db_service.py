"""Service to save games to DynamoDB"""

from typing import List, Optional
from datetime import datetime

from app.services.game_manager import GameState
from app.services.dynamodb_service import dynamodb_service
import json


def save_game_to_db(game_state: GameState, user_id: str = None):
    """Save a completed game to DynamoDB user's game history"""
    if not game_state.over:
        return  # Only save completed games

    # Prepare game data
    game_data = {
        "game_id": game_state.game_id,
        "game_type": game_state.game_type,
        "result": game_state.result,
        "white_model": game_state.white_model,
        "black_model": game_state.black_model,
        "white_tokens": game_state.white_tokens,
        "black_tokens": game_state.black_tokens,
        "total_moves": len(game_state.moves),
        "completed_at": datetime.utcnow().isoformat() + "Z",
    }

    # If user_id is provided, save to that user's history
    # Otherwise, we could infer from the models or skip user association
    if user_id:
        dynamodb_service.add_game_result(user_id, game_state.game_id, game_data)


def get_user_games(user_id: str) -> List[dict]:
    """Get all games for a user from DynamoDB"""
    user_data = dynamodb_service.get_user(user_id)
    if not user_data:
        return []

    game_list = user_data.get("game_list", {})
    # Convert the map to a list of games
    games = []
    for game_id, game_data in game_list.items():
        game_data["game_id"] = game_id  # Add the ID to the game data
        games.append(game_data)

    # Sort by completed_at descending (most recent first)
    games.sort(key=lambda x: x.get("completed_at", ""), reverse=True)
    return games
