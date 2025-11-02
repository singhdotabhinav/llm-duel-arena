from __future__ import annotations

import chess
from typing import Optional, List, Dict


class ChessEngine:
    def __init__(self, fen: Optional[str] = None) -> None:
        self.board = chess.Board(fen) if fen else chess.Board()

    def reset(self, fen: Optional[str] = None) -> None:
        self.board = chess.Board(fen) if fen else chess.Board()

    def get_fen(self) -> str:
        return self.board.fen()

    def legal_moves_uci(self) -> List[str]:
        return [m.uci() for m in self.board.legal_moves]

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

    def push_uci(self, uci: str) -> bool:
        try:
            move = chess.Move.from_uci(uci)
        except ValueError:
            return False
        if move not in self.board.legal_moves:
            return False
        self.board.push(move)
        return True

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

