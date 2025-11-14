from pydantic import BaseModel, Field
from typing import Optional, List, Literal, Dict

Side = Literal["white", "black"]
GameType = Literal["chess", "tic_tac_toe", "rock_paper_scissors", "racing", "word_association_clash"]


class CreateGameRequest(BaseModel):
    game_type: GameType = "chess"
    white_model: Optional[str] = None
    black_model: Optional[str] = None
    initial_state: Optional[str] = None  # FEN for chess, board string for TTT
    fen: Optional[str] = None  # Deprecated, use initial_state


class MoveRequest(BaseModel):
    move: str = Field(..., description="Move string in UCI format (e2e4)")


class MoveRecord(BaseModel):
    ply: int
    side: Side
    move_uci: str
    move_san: Optional[str] = None
    model_name: Optional[str] = None
    error: Optional[str] = None
    from_square: Optional[str] = None
    to_square: Optional[str] = None
    captured_piece: Optional[str] = None
    tokens_used: int = 0


class GameState(BaseModel):
    game_id: str
    game_type: GameType
    state: str  # Generic state (renamed from fen)
    fen: str = ""  # Deprecated, keep for backward compatibility
    turn: Side
    over: bool
    result: Dict[str, str]
    moves: List[MoveRecord] = []
    white_model: Optional[str] = None
    black_model: Optional[str] = None
    white_tokens: int = 0
    black_tokens: int = 0
