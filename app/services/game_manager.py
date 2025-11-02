from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Literal

from .base_game import BaseGameEngine
from .chess_engine import ChessEngine
from .tic_tac_toe_engine import TicTacToeEngine
from .rps_engine import RPSEngine

Side = Literal["white", "black"]
GameType = Literal["chess", "tic_tac_toe", "rock_paper_scissors"]


@dataclass
class MoveRecord:
    ply: int
    side: Side
    move_uci: str
    move_san: str | None
    model_name: str | None
    error: str | None = None
    from_square: str | None = None
    to_square: str | None = None
    captured_piece: str | None = None  # single char piece symbol from python-chess: 'p','n','b','r','q','k' (lowercase for black)


@dataclass
class GameState:
    game_id: str
    game_type: GameType
    state: str  # Generic state (FEN for chess, board string for TTT)
    turn: Side
    over: bool
    result: Dict[str, str]
    moves: List[MoveRecord] = field(default_factory=list)
    white_model: str | None = None
    black_model: str | None = None


class GameManager:
    def __init__(self) -> None:
        self._games: Dict[str, GameState] = {}
        self._engines: Dict[str, BaseGameEngine] = {}
    
    def _create_engine(self, game_type: GameType, initial_state: Optional[str] = None) -> BaseGameEngine:
        if game_type == "chess":
            return ChessEngine(initial_state)
        elif game_type == "tic_tac_toe":
            return TicTacToeEngine(initial_state)
        elif game_type == "rock_paper_scissors":
            return RPSEngine(initial_state)
        else:
            raise ValueError(f"Unknown game type: {game_type}")

    def create_game(self, game_type: GameType, white_model: Optional[str], black_model: Optional[str], initial_state: Optional[str] = None) -> GameState:
        game_id = uuid.uuid4().hex
        engine = self._create_engine(game_type, initial_state)
        self._engines[game_id] = engine
        
        turn = engine.get_turn() if hasattr(engine, 'get_turn') else ("white" if game_type == "chess" else "white")
        
        state = GameState(
            game_id=game_id,
            game_type=game_type,
            state=engine.get_state(),
            turn=turn,
            over=engine.is_game_over(),
            result=engine.result(),
            white_model=white_model,
            black_model=black_model,
        )
        self._games[game_id] = state
        return state

    def get_state(self, game_id: str) -> Optional[GameState]:
        state = self._games.get(game_id)
        if not state:
            return None
        engine = self._engines[game_id]
        state.state = engine.get_state()
        state.turn = engine.get_turn() if hasattr(engine, 'get_turn') else state.turn
        state.over = engine.is_game_over()
        state.result = engine.result()
        return state

    def push_move(self, game_id: str, move_str: str, model_name: Optional[str] = None, error: Optional[str] = None) -> Optional[GameState]:
        state = self._games.get(game_id)
        if not state:
            return None
        engine = self._engines[game_id]
        side: Side = engine.get_turn() if hasattr(engine, 'get_turn') else state.turn

        from_square = None
        to_square = None
        captured_symbol: str | None = None
        
        # Chess-specific capture detection
        if state.game_type == "chess" and len(move_str) >= 4:
            from_square = move_str[:2]
            to_square = move_str[2:4]
            if to_square:
                try:
                    import chess
                    square_idx = chess.parse_square(to_square)
                    piece = engine.board.piece_at(square_idx)  # type: ignore
                    if piece is not None:
                        captured_symbol = piece.symbol()
                except Exception:
                    captured_symbol = None
        elif state.game_type == "tic_tac_toe":
            # For TTT, move is "row,col"
            parts = move_str.split(',')
            if len(parts) == 2:
                from_square = move_str
                to_square = move_str

        ok = engine.push_move(move_str)
        san = None
        if ok and state.game_type == "chess":
            try:
                last = engine.board.pop()  # type: ignore
                san = engine.board.san(last)  # type: ignore
                engine.board.push(last)  # type: ignore
            except Exception:
                san = None
        
        rec = MoveRecord(
            ply=len(state.moves) + 1,
            side=side,
            move_uci=move_str,
            move_san=san,
            model_name=model_name,
            error=None if ok else (error or "illegal move"),
            from_square=from_square,
            to_square=to_square,
            captured_piece=captured_symbol if ok else None,
        )
        state.moves.append(rec)
        return self.get_state(game_id)

    def reset(self, game_id: str, initial_state: Optional[str] = None) -> Optional[GameState]:
        if game_id not in self._games:
            return None
        engine = self._engines[game_id]
        engine.reset(initial_state)
        self._games[game_id].moves.clear()
        return self.get_state(game_id)


game_manager = GameManager()
