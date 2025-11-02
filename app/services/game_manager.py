from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Literal

from .chess_engine import ChessEngine

Side = Literal["white", "black"]


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
    fen: str
    turn: Side
    over: bool
    result: Dict[str, str]
    moves: List[MoveRecord] = field(default_factory=list)
    white_model: str | None = None
    black_model: str | None = None


class GameManager:
    def __init__(self) -> None:
        self._games: Dict[str, GameState] = {}
        self._engines: Dict[str, ChessEngine] = {}

    def create_game(self, white_model: Optional[str], black_model: Optional[str], fen: Optional[str] = None) -> GameState:
        game_id = uuid.uuid4().hex
        engine = ChessEngine(fen=fen)
        self._engines[game_id] = engine
        state = GameState(
            game_id=game_id,
            fen=engine.get_fen(),
            turn="white" if engine.board.turn else "black",
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
        state.fen = engine.get_fen()
        state.turn = "white" if engine.board.turn else "black"
        state.over = engine.is_game_over()
        state.result = engine.result()
        return state

    def push_move(self, game_id: str, move_uci: str, model_name: Optional[str] = None, error: Optional[str] = None) -> Optional[GameState]:
        state = self._games.get(game_id)
        if not state:
            return None
        engine = self._engines[game_id]
        side: Side = "white" if engine.board.turn else "black"

        from_square = move_uci[:2] if len(move_uci) >= 4 else None
        to_square = move_uci[2:4] if len(move_uci) >= 4 else None
        captured_symbol: str | None = None
        if to_square:
            try:
                import chess

                square_idx = chess.parse_square(to_square)
                piece = engine.board.piece_at(square_idx)
                if piece is not None:
                    # piece.symbol() gives 'p','n','b','r','q','k' for black, uppercase for white
                    captured_symbol = piece.symbol()
            except Exception:
                captured_symbol = None

        ok = engine.push_uci(move_uci)
        san = None
        if ok:
            try:
                last = engine.board.pop()
                san = engine.board.san(last)
                engine.board.push(last)
            except Exception:
                san = None
        rec = MoveRecord(
            ply=len(state.moves) + 1,
            side=side,
            move_uci=move_uci,
            move_san=san,
            model_name=model_name,
            error=None if ok else (error or "illegal move"),
            from_square=from_square,
            to_square=to_square,
            captured_piece=captured_symbol if ok else None,
        )
        state.moves.append(rec)
        return self.get_state(game_id)

    def reset(self, game_id: str, fen: Optional[str] = None) -> Optional[GameState]:
        if game_id not in self._games:
            return None
        engine = self._engines[game_id]
        engine.reset(fen)
        self._games[game_id].moves.clear()
        return self.get_state(game_id)


game_manager = GameManager()
