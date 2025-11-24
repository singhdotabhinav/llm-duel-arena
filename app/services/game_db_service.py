"""Service to save games to database"""
from sqlalchemy.orm import Session
from ..database import Game, SessionLocal
from .game_manager import GameState as GameManagerState
import json


def save_game_to_db(game_state: GameManagerState, user_id: str = None):
    """Save or update a game in the database"""
    db = SessionLocal()
    try:
        # Check if game already exists
        game = db.query(Game).filter(Game.id == game_state.game_id).first()
        
        # Prepare game state JSON
        state_json = json.dumps({
            "state": game_state.state,
            "moves": [
                {
                    "ply": m.ply,
                    "side": m.side,
                    "move_uci": m.move_uci,
                    "move_san": m.move_san,
                    "model_name": m.model_name,
                    "error": m.error
                }
                for m in game_state.moves
            ]
        })
        
        if game:
            # Update existing game
            game.result = game_state.result.get("result", "")
            game.winner = game_state.result.get("winner")
            game.moves_count = len(game_state.moves)
            game.is_over = 1 if game_state.over else 0
            game.white_tokens = getattr(game_state, 'white_tokens', 0)
            game.black_tokens = getattr(game_state, 'black_tokens', 0)
            game.game_state = state_json
            
            # If user_id not provided, use existing one
            if not user_id:
                user_id = game.user_id
        else:
            # Create new game
            game = Game(
                id=game_state.game_id,
                user_id=user_id,
                game_type=game_state.game_type,
                white_model=game_state.white_model,
                black_model=game_state.black_model,
                result=game_state.result.get("result", ""),
                winner=game_state.result.get("winner"),
                moves_count=len(game_state.moves),
                is_over=1 if game_state.over else 0,
                white_tokens=getattr(game_state, 'white_tokens', 0),
                black_tokens=getattr(game_state, 'black_tokens', 0),
                game_state=state_json
            )
            db.add(game)
        
        db.commit()
        
        # Save to DynamoDB if game is over and user is linked
        if game_state.over and user_id:
            print(f"[GameDB] Game {game_state.game_id} is over. User ID: {user_id}. Attempting DynamoDB save...")
            try:
                from ..database import User
                from .dynamodb_service import dynamodb_service
                
                user = db.query(User).filter(User.id == user_id).first()
                if user and user.email:
                    print(f"[GameDB] Found user {user.email}. Saving game result...")
                    game_data = {
                        "game": game_state.game_type,
                        "p1": game_state.white_model or "Unknown",
                        "p2": game_state.black_model or "Unknown",
                        "result": game_state.result.get("winner") or "Draw"
                    }
                    success = dynamodb_service.add_game_result(user.email, game_state.game_id, game_data)
                    if success:
                        print(f"[GameDB] Successfully saved to DynamoDB for {user.email}")
                    else:
                        print(f"[GameDB] Failed to save to DynamoDB (service returned False)")
                else:
                    print(f"[GameDB] User {user_id} not found or has no email.")
            except Exception as e:
                # Don't fail the main save if DynamoDB fails
                print(f"[GameDB] Exception saving to DynamoDB: {e}")
        else:
            print(f"[GameDB] Not saving to DynamoDB. Over: {game_state.over}, User ID: {user_id}")
                
        return game
    finally:
        db.close()


def get_user_games(user_id: str, limit: int = 100):
    """Get all games for a user"""
    db = SessionLocal()
    try:
        games = db.query(Game).filter(Game.user_id == user_id).order_by(Game.created_at.desc()).limit(limit).all()
        return games
    finally:
        db.close()


def get_game_from_db(game_id: str):
    """Get a single game by ID"""
    db = SessionLocal()
    try:
        game = db.query(Game).filter(Game.id == game_id).first()
        return game
    finally:
        db.close()

