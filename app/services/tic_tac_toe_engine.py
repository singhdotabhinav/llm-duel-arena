from __future__ import annotations

from typing import List, Dict, Optional

from .base_game import BaseGameEngine


class TicTacToeEngine(BaseGameEngine):
    """Tic Tac Toe game engine"""

    def __init__(self, initial_state: Optional[str] = None) -> None:
        self.board = self._parse_state(initial_state) if initial_state else [["", "", ""] for _ in range(3)]

        # Determine current player based on board state
        # Count X's and O's to figure out whose turn it is
        x_count = sum(row.count("X") for row in self.board)
        o_count = sum(row.count("O") for row in self.board)

        # If equal, X goes next. If X has one more, O goes next.
        if x_count == o_count:
            self.current_player = "X"
        else:
            self.current_player = "O"

    def _parse_state(self, state: str) -> List[List[str]]:
        """Parse state string like 'X-O-X-O-X-O-X-O-X' or '---------'"""
        board = [["", "", ""] for _ in range(3)]
        if state:
            cells = state.replace("|", "").replace("\n", "").split("-")[:9]
            for i, cell in enumerate(cells):
                row = i // 3
                col = i % 3
                board[row][col] = cell.strip() if cell.strip() and cell.strip() != "-" else ""
        return board

    def reset(self, initial_state: Optional[str] = None) -> None:
        self.board = self._parse_state(initial_state) if initial_state else [["", "", ""] for _ in range(3)]
        self.current_player = "X"

    def get_state(self) -> str:
        """Return board state as string: row1-row2-row3 where empty cells are empty strings"""
        cells = []
        for row in self.board:
            for cell in row:
                cells.append(cell if cell else "")
        return "-".join(cells)

    def legal_moves(self) -> List[str]:
        """Return legal moves as 'row,col' format: ['0,0', '0,1', ...]"""
        moves = []
        for row in range(3):
            for col in range(3):
                if not self.board[row][col]:
                    moves.append(f"{row},{col}")
        return moves

    def is_game_over(self) -> bool:
        """Check if game is over (win or draw)"""
        return self._check_winner() != None or all(all(cell for cell in row) for row in self.board)

    def _check_winner(self) -> Optional[str]:
        """Check for winner. Returns 'X', 'O', or None"""
        # Check rows
        for row in self.board:
            if row[0] and row[0] == row[1] == row[2]:
                return row[0]
        # Check columns
        for col in range(3):
            if self.board[0][col] and self.board[0][col] == self.board[1][col] == self.board[2][col]:
                return self.board[0][col]
        # Check diagonals
        if self.board[0][0] and self.board[0][0] == self.board[1][1] == self.board[2][2]:
            return self.board[0][0]
        if self.board[0][2] and self.board[0][2] == self.board[1][1] == self.board[2][0]:
            return self.board[0][2]
        return None

    def result(self) -> Dict[str, str]:
        """Get game result"""
        if not self.is_game_over():
            return {"status": "ongoing", "result": "*"}
        winner = self._check_winner()
        if winner:
            return {"status": "win", "winner": "white" if winner == "X" else "black", "result": f"{winner}-wins"}
        return {"status": "draw", "result": "1/2-1/2"}

    def push_move(self, move: str) -> bool:
        """Apply move in format 'row,col' or 'row,col'"""
        try:
            parts = move.split(",")
            if len(parts) != 2:
                return False
            row, col = int(parts[0].strip()), int(parts[1].strip())
            if not (0 <= row < 3 and 0 <= col < 3):
                return False
            if self.board[row][col]:
                return False
            self.board[row][col] = self.current_player
            self.current_player = "O" if self.current_player == "X" else "X"
            return True
        except (ValueError, IndexError):
            return False

    def get_turn(self) -> str:
        """Get current player"""
        return "white" if self.current_player == "X" else "black"
