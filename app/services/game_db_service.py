"""Service to save games to DynamoDB"""

import json
import logging
from datetime import datetime
from typing import List, Optional

from app.services.dynamodb_service import dynamodb_service
from app.services.game_manager import GameState

logger = logging.getLogger(__name__)


def save_game_to_db(game_state: GameState, user_id: str = None):
    """Save a completed game to DynamoDB user's game history"""
    if not game_state.over:
        logger.debug(f"Game {game_state.game_id} not over yet (over={game_state.over}) - skipping save")
        return  # Only save completed games

    # Use user_id from game_state if not provided
    # user_id should be the email address (used as DynamoDB key)
    email = user_id or game_state.user_id
    if not email:
        logger.warning(
            f"Game {game_state.game_id} completed but no user_id - skipping user history save. "
            f"user_id param: {user_id}, game_state.user_id: {game_state.user_id}"
        )
        return

    logger.info(f"Saving game {game_state.game_id} to user history: {email}")
    logger.info(f"Using DynamoDB table: {dynamodb_service.table_name}")

    # Prepare game data
    # Store full result dict for proper structure, but also extract string for backward compatibility
    result_str = game_state.result.get("winner") or game_state.result.get("result") or "draw"
    game_data = {
        "game_id": game_state.game_id,
        "game_type": game_state.game_type,  # Primary key for game type
        "game": game_state.game_type,  # Keep 'game' key for backward compatibility
        "p1": game_state.white_model or "Unknown",  # Keep 'p1' key for backward compatibility
        "p2": game_state.black_model or "Unknown",  # Keep 'p2' key for backward compatibility
        "result": result_str,  # String result for backward compatibility
        "result_dict": game_state.result,  # Full result dict with status, winner, result
        "white_model": game_state.white_model,
        "black_model": game_state.black_model,
        "white_tokens": game_state.white_tokens,
        "black_tokens": game_state.black_tokens,
        "total_moves": len(game_state.moves),
        "completed_at": datetime.utcnow().isoformat() + "Z",
    }

    # Save to user's history (email is used as the key)
    success = dynamodb_service.add_game_result(email, game_state.game_id, game_data)
    if not success:
        logger.error(f"Failed to save game {game_state.game_id} to user history for {email}")
    else:
        logger.info(f"Successfully saved game {game_state.game_id} to user history for {email}")


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
