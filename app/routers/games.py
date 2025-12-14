from fastapi import APIRouter, HTTPException, Request, Depends
from typing import Optional
from ..services.game_manager import game_manager
from ..services.match_runner import match_runner
from ..services.game_db_service import save_game_to_db, get_user_games
from ..schemas import CreateGameRequest, MoveRequest, GameState as GameStateSchema, MoveRecord as MoveRecordSchema
from ..core.auth import get_current_user_obj as get_current_user

router = APIRouter()


def _to_schema(state) -> GameStateSchema:
    return GameStateSchema(
        game_id=state.game_id,
        game_type=state.game_type,
        state=state.state,
        fen=state.state,  # Keep for backward compatibility
        turn=state.turn,  # type: ignore
        over=state.over,
        result=state.result,
        moves=[
            MoveRecordSchema(
                ply=m.ply,
                side=m.side,  # type: ignore
                move_uci=m.move_uci,
                move_san=m.move_san,
                model_name=m.model_name,
                error=m.error,
                from_square=m.from_square,
                to_square=m.to_square,
                captured_piece=m.captured_piece,
                tokens_used=getattr(m, "tokens_used", 0),
            )
            for m in state.moves
        ],
        white_model=state.white_model,
        black_model=state.black_model,
        white_tokens=getattr(state, "white_tokens", 0),
        black_tokens=getattr(state, "black_tokens", 0),
    )


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/list")
async def list_games():
    """List all games with summary info"""
    games_list = []
    # GameManager is now stateless - use database service to list games
    # For now, return empty list if database is not available (e.g., in tests)
    # In production, this would scan DynamoDB table
    try:
        from ..services.active_game_db import active_game_service

        # If database is not available (e.g., in tests), return empty list
        if not active_game_service.table:
            return {"games": []}

        # Scan DynamoDB table to get all games
        # Note: This is a simple scan - in production you might want pagination
        response = active_game_service.table.scan()
        items = response.get("Items", [])

        for item in items:
            games_list.append(
                {
                    "game_id": item.get("game_id", ""),
                    "game_type": item.get("game_type", "unknown"),
                    "white_model": item.get("white_model") or "Unknown",
                    "black_model": item.get("black_model") or "Unknown",
                    "moves_count": len(item.get("moves", [])),
                    "over": item.get("over", False),
                    "result": item.get("result", {}),
                    "turn": item.get("turn", "white"),
                }
            )
    except Exception as e:
        # Log error but return empty list to avoid breaking the endpoint
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(f"Error listing games: {e}")
        return {"games": []}

    return {"games": games_list}


@router.get("/my-games")
async def get_my_games(request: Request):
    """Get games for the logged-in user from DynamoDB"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Fetch from DynamoDB
    from ..services.dynamodb_service import dynamodb_service

    # Use email from user object (user.email or user.id if email not available)
    user_email = (
        user.email
        if hasattr(user, "email") and user.email
        else (user.get("email") if isinstance(user, dict) else user.id)
    )
    user_data = dynamodb_service.get_user(user_email)

    games_list = []
    if user_data and "game_list" in user_data:
        # game_list is a map of game_id -> game_data
        for game_id, game_info in user_data["game_list"].items():
            # Determine winner/result structure to match frontend expectation
            # Frontend expects: "result": {"result": "...", "winner": "..."}
            # DynamoDB has: "result": "Model Name" (string)

            # We need to adapt the DynamoDB format to what the frontend expects
            # based on the previous SQL implementation:
            # "result": {"result": game.result, "winner": game.winner}

            # In DynamoDB we stored "result" as the winner model name.
            # Let's reconstruct a compatible structure.
            result_str = game_info.get("result", "Unknown")

            games_list.append(
                {
                    "game_id": game_id,
                    "game_type": game_info.get("game", "unknown"),
                    "white_model": game_info.get("p1", "Unknown"),
                    "black_model": game_info.get("p2", "Unknown"),
                    "moves_count": 0,  # Not stored in simple DynamoDB schema
                    "over": True,  # All games in history are over
                    "result": {"result": result_str, "winner": result_str},
                    "created_at": None,  # Not stored in simple DynamoDB schema
                }
            )

    return {"games": games_list}


@router.post("/random_duel")
async def random_duel(req: CreateGameRequest, request: Request):
    """Start a random duel with default models"""
    import random
    import logging

    logger = logging.getLogger(__name__)
    logger.info(f"Random duel requested with game_type: {req.game_type}")

    models = [
        "ollama:llama3.1:latest",
        "ollama:mistral-nemo:latest",
        "ollama:deepseek-r1:1.5b",
        "ollama:llama3.2:latest",
        "ollama:gpt-oss:latest",
        "ollama:gemma3:270m",
    ]
    white = random.choice(models)
    black = random.choice([m for m in models if m != white])

    game_type = req.game_type if req.game_type else "chess"
    initial_state = req.initial_state or req.fen

    logger.info(f"Creating {game_type} game with {white} vs {black}")
    # Get user before creating game so we can store user_id
    user = get_current_user(request)
    user_id = user.id if user else None
    state = game_manager.create_game(
        game_type, white, black, initial_state, user_id=user_id
    )

    # Note: Game will be saved to user's history when it completes (in match_runner)

    # Don't auto-start - let user click Start button
    # match_runner.start(state.game_id, white, black)

    return {"game_id": state.game_id, "game_type": state.game_type, "white_model": white, "black_model": black}


@router.post("/", response_model=GameStateSchema)
async def create_game(req: CreateGameRequest, request: Request):
    game_type = req.game_type or "chess"
    initial_state = req.initial_state or req.fen
    # Get user before creating game so we can store user_id
    user = get_current_user(request)
    user_id = user.id if user else None
    state = game_manager.create_game(
        game_type, req.white_model, req.black_model, initial_state, user_id=user_id
    )

    # Note: Game will be saved to user's history when it completes (in match_runner)

    return _to_schema(state)


@router.get("/{game_id}", response_model=GameStateSchema)
async def get_state(game_id: str):
    state = game_manager.get_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Game not found")
    print(f"[API] Returning state for {game_id}: White={state.white_tokens}, Black={state.black_tokens}")
    return _to_schema(state)


@router.post("/{game_id}/move", response_model=GameStateSchema)
async def post_move(game_id: str, req: MoveRequest, request: Request):
    state = game_manager.get_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Game not found")
    updated = game_manager.push_move(game_id, req.move, model_name="manual")

    # Update database if user is logged in
    user = get_current_user(request)
    if user:
        save_game_to_db(updated, user.id)

    return _to_schema(updated)


@router.post("/{game_id}/reset", response_model=GameStateSchema)
async def reset_game(game_id: str, req: Optional[CreateGameRequest] = None):
    # Accept initial_state in request body for custom prompts
    initial_state = req.initial_state if req else None
    state = game_manager.reset(game_id, initial_state)
    if not state:
        raise HTTPException(status_code=404, detail="Game not found")
    return _to_schema(state)


@router.post("/{game_id}/process_turn")
async def process_turn(game_id: str):
    """
    Trigger the AI to process a single turn.
    Called by the client when it detects it's the AI's turn.
    """
    result = await match_runner.process_turn(game_id)
    return result


@router.post("/{game_id}/start_autoplay")
async def start_autoplay(game_id: str, req: CreateGameRequest):
    # Deprecated: Client drives the game now.
    # We just ensure the game exists.
    state = game_manager.get_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Game not found")
    return {"status": "started"}


@router.post("/{game_id}/pause")
async def pause_autoplay(game_id: str):
    # Deprecated
    return {"status": "paused"}


@router.post("/{game_id}/resume")
async def resume_autoplay(game_id: str):
    # Deprecated
    return {"status": "resumed"}
