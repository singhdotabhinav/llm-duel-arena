from fastapi import APIRouter, HTTPException
from ..services.game_manager import game_manager
from ..services.match_runner import match_runner
from ..schemas import CreateGameRequest, MoveRequest, GameState as GameStateSchema, MoveRecord as MoveRecordSchema

router = APIRouter()


def _to_schema(state) -> GameStateSchema:
    return GameStateSchema(
        game_id=state.game_id,
        fen=state.fen,
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
            )
            for m in state.moves
        ],
        white_model=state.white_model,
        black_model=state.black_model,
    )


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.post("/", response_model=GameStateSchema)
async def create_game(req: CreateGameRequest):
    state = game_manager.create_game(req.white_model, req.black_model, req.fen)
    return _to_schema(state)


@router.get("/{game_id}", response_model=GameStateSchema)
async def get_state(game_id: str):
    state = game_manager.get_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Game not found")
    return _to_schema(state)


@router.post("/{game_id}/move", response_model=GameStateSchema)
async def post_move(game_id: str, req: MoveRequest):
    state = game_manager.get_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Game not found")
    updated = game_manager.push_move(game_id, req.move, model_name="manual")
    return _to_schema(updated)


@router.post("/{game_id}/reset", response_model=GameStateSchema)
async def reset_game(game_id: str):
    state = game_manager.reset(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Game not found")
    return _to_schema(state)


@router.post("/{game_id}/start_autoplay")
async def start_autoplay(game_id: str, req: CreateGameRequest):
    state = game_manager.get_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Game not found")
    white = req.white_model or state.white_model
    black = req.black_model or state.black_model
    if not white or not black:
        raise HTTPException(status_code=400, detail="Both models must be specified")
    match_runner.start(game_id, white, black)
    return {"status": "started"}


@router.post("/{game_id}/pause")
async def pause_autoplay(game_id: str):
    match_runner.pause(game_id)
    return {"status": "paused"}


@router.post("/{game_id}/resume")
async def resume_autoplay(game_id: str):
    match_runner.resume(game_id)
    return {"status": "resumed"}
