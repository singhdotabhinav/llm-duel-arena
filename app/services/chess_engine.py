from __future__ import annotations

import chess
from typing import Optional, List, Dict

from .base_game import BaseGameEngine


class ChessEngine(BaseGameEngine):
    def __init__(self, fen: Optional[str] = None) -> None:
        self.board = chess.Board(fen) if fen else chess.Board()

    def reset(self, initial_state: Optional[str] = None) -> None:
        self.board = chess.Board(initial_state) if initial_state else chess.Board()

    def get_state(self) -> str:
        return self.board.fen()

    def get_fen(self) -> str:  # Keep for backward compatibility
        return self.get_state()

    def legal_moves(self) -> List[str]:
        return [m.uci() for m in self.board.legal_moves]

    def legal_moves_uci(self) -> List[str]:  # Keep for backward compatibility
        return self.legal_moves()

    def is_game_over(self) -> bool:
        return self.board.is_game_over()

    def result(self) -> Dict[str, str]:
        if not self.board.is_game_over():
            return {"status": "ongoing", "result": "*"}
        res = self.board.result(claim_draw=True)
        if res == "1-0":
            return {"status": "mate", "winner": "white", "result": res}
        if res == "0-1":
            return {"status": "mate", "winner": "black", "result": res}
        return {"status": "draw", "result": res}

    def push_move(self, move: str) -> bool:
        try:
            move_obj = chess.Move.from_uci(move)
        except ValueError:
            return False
        if move_obj not in self.board.legal_moves:
            return False
        self.board.push(move_obj)
        return True

    def push_uci(self, uci: str) -> bool:  # Keep for backward compatibility
        return self.push_move(uci)

    def get_turn(self) -> str:
        """Get current player"""
        return "white" if self.board.turn else "black"

    def san_to_uci(self, san: str) -> Optional[str]:
        try:
            move = self.board.parse_san(san)
            return move.uci()
        except Exception:
            return None

    def uci_to_san(self, uci: str) -> Optional[str]:
        try:
            move = chess.Move.from_uci(uci)
            if move not in self.board.legal_moves:
                return None
            return self.board.san(move)
        except Exception:
            return None
