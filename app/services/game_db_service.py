"""Service to save games to DynamoDB"""

from typing import List, Optional
from datetime import datetime
import logging

from app.services.game_manager import GameState
from app.services.dynamodb_service import dynamodb_service
import json

logger = logging.getLogger(__name__)


def save_game_to_db(game_state: GameState, user_id: str = None):
    """Save a completed game to DynamoDB user's game history"""
    if not game_state.over:
        return  # Only save completed games

    # Use user_id from game_state if not provided
    email = user_id or game_state.user_id
    if not email:
        logger.warning(f"Game {game_state.game_id} completed but no user_id - skipping user history save")
        return

    # Prepare game data
    game_data = {
        "game_id": game_state.game_id,
        "game": game_state.game_type,  # Use 'game' key to match frontend expectation
        "p1": game_state.white_model or "Unknown",  # Use 'p1' key to match frontend expectation
        "p2": game_state.black_model or "Unknown",  # Use 'p2' key to match frontend expectation
        "result": game_state.result.get("winner") or game_state.result.get("result") or "draw",  # Extract winner/result string
        "white_model": game_state.white_model,
        "black_model": game_state.black_model,
        "white_tokens": game_state.white_tokens,
        "black_tokens": game_state.black_tokens,
        "total_moves": len(game_state.moves),
        "completed_at": datetime.utcnow().isoformat() + "Z",
    }

    # Save to user's history (email is used as the key)
    dynamodb_service.add_game_result(email, game_state.game_id, game_data)


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
