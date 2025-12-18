from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional

from .base_game import BaseGameEngine
from .chess_engine import ChessEngine
from .racing_engine import RacingEngine
from .rps_engine import RPSEngine
from .tic_tac_toe_engine import TicTacToeEngine
from .word_association_engine import WordAssociationEngine

logger = logging.getLogger(__name__)

Side = Literal["white", "black"]
GameType = Literal[
    "chess", "tic_tac_toe", "rock_paper_scissors", "racing", "word_association_clash"
]


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
    captured_piece: str | None = (
        None  # single char piece symbol from python-chess: 'p','n','b','r','q','k' (lowercase for black)
    )
    tokens_used: int = 0  # Tokens used for this move


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
    white_tokens: int = 0  # Total tokens used by white model
    black_tokens: int = 0  # Total tokens used by black model
    user_id: str | None = None  # User who created the game (email or Cognito sub)


class GameManager:
    def __init__(self) -> None:
        # Stateless manager - no in-memory storage
        from .active_game_db import active_game_service

        self.db = active_game_service

    def _create_engine(self, game_type: GameType, initial_state: Optional[str] = None) -> BaseGameEngine:
        if game_type == "chess":
            return ChessEngine(initial_state)
        elif game_type == "tic_tac_toe":
            return TicTacToeEngine(initial_state)
        elif game_type == "rock_paper_scissors":
            return RPSEngine(initial_state)
        elif game_type == "racing":
            return RacingEngine(initial_state)
        elif game_type == "word_association_clash":
            return WordAssociationEngine(initial_state)
        else:
            raise ValueError(f"Unknown game type: {game_type}")

    def create_game(
        self,
        game_type: GameType,
        white_model: Optional[str],
        black_model: Optional[str],
        initial_state: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> GameState:
        game_id = uuid.uuid4().hex
        engine = self._create_engine(game_type, initial_state)

        turn = (
            engine.get_turn()
            if hasattr(engine, "get_turn")
            else ("white" if game_type == "chess" else "white")
        )

        state = GameState(
            game_id=game_id,
            game_type=game_type,
            state=engine.get_state(),
            turn=turn,
            over=engine.is_game_over(),
            result=engine.result(),
            white_model=white_model,
            black_model=black_model,
            user_id=user_id,
        )

        # Save to DynamoDB
        self.db.save_state(state)
        return state

    def get_state(self, game_id: str) -> Optional[GameState]:
        # Load from DynamoDB
        state = self.db.load_state(game_id)
        if not state:
            return None

        # We don't need to reconstruct the engine just to return state,
        # unless we need to compute derived properties.
        # But for consistency with previous implementation (which refreshed state from engine),
        # let's trust the saved state is accurate.
        return state

    def push_move(
        self,
        game_id: str,
        move_str: str,
        model_name: Optional[str] = None,
        error: Optional[str] = None,
        tokens_used: int = 0,
    ) -> Optional[GameState]:
        # Load state
        state = self.db.load_state(game_id)
        if not state:
            return None

        # Reconstruct engine
        engine = self._create_engine(state.game_type, state.state)

        # For some games (like Word Association), we might need more context than just 'state' string
        # if the engine relies on history not fully captured in the simple state string.
        # But our engines seem to serialize everything into get_state().
        # Exception: WordAssociationEngine might need history.
        # Let's assume get_state() returns full JSON for complex games.

        side: Side = engine.get_turn() if hasattr(engine, "get_turn") else state.turn
        logger.debug(f"[GameManager] Before move: side={side}, state.turn={state.turn}")

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
            parts = move_str.split(",")
            if len(parts) == 2:
                from_square = move_str
                to_square = move_str

        # Apply move
        ok = engine.push_move(move_str)

        san = None
        if ok and state.game_type == "chess":
            try:
                # This is tricky: engine.board is now updated.
                # We need the move SAN. python-chess usually gives SAN before push or via move object.
                # But we already pushed.
                # Let's just try to get it if possible, or skip.
                # Actually, our previous code popped, got san, pushed back.
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
            tokens_used=tokens_used,
        )
        state.moves.append(rec)

        # Update total token counts
        if side == "white":
            state.white_tokens += tokens_used
            logger.debug(
                f"[GameManager] Updated White Tokens: {state.white_tokens} (added {tokens_used})"
            )
        else:
            state.black_tokens += tokens_used
            logger.debug(
                f"[GameManager] Updated Black Tokens: {state.black_tokens} (added {tokens_used})"
            )

        # Update state object with new engine state
        state.state = engine.get_state()
        state.turn = engine.get_turn() if hasattr(engine, "get_turn") else state.turn
        logger.debug(
            f"[GameManager] After move: state.turn={state.turn}, state.state={state.state}"
        )
        state.over = engine.is_game_over()
        state.result = engine.result()

        # Save updated state
        self.db.save_state(state)

        return state

    def reset(self, game_id: str, initial_state: Optional[str] = None) -> Optional[GameState]:
        state = self.db.load_state(game_id)
        if not state:
            return None

        engine = self._create_engine(state.game_type, initial_state)

        # Update state
        state.state = engine.get_state()
        state.turn = engine.get_turn() if hasattr(engine, "get_turn") else state.turn
        state.over = engine.is_game_over()
        state.result = engine.result()
        state.moves = []
        state.white_tokens = 0
        state.black_tokens = 0

        self.db.save_state(state)
        return state


game_manager = GameManager()
