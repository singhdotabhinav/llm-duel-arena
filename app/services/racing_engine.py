from __future__ import annotations

from typing import List, Dict, Optional
from .base_game import BaseGameEngine


class RacingEngine(BaseGameEngine):
    """Sprint Racing game engine - limited moves, fastest to finish wins"""

    TRACK_LENGTH = 100  # Distance to finish line
    MAX_MOVES = 20  # Maximum moves per racer

    def __init__(self, initial_state: Optional[str] = None) -> None:
        if initial_state:
            self._parse_state(initial_state)
        else:
            self.white_position = 0
            self.black_position = 0
            self.white_speed = 0
            self.black_speed = 0
            self.white_moves = 0
            self.black_moves = 0
        self.current_player = "white"

    def _parse_state(self, state: str) -> None:
        """Parse state string like 'white_pos:white_speed:white_moves|black_pos:black_speed:black_moves|turn'"""
        try:
            parts = state.split("|")
            white_data = parts[0].split(":")
            black_data = parts[1].split(":")

            self.white_position = int(white_data[0])
            self.white_speed = int(white_data[1])
            self.white_moves = int(white_data[2])

            self.black_position = int(black_data[0])
            self.black_speed = int(black_data[1])
            self.black_moves = int(black_data[2])

            self.current_player = parts[2] if len(parts) > 2 else "white"
        except (IndexError, ValueError):
            # Invalid state, reset to defaults
            self.white_position = 0
            self.black_position = 0
            self.white_speed = 0
            self.black_speed = 0
            self.white_moves = 0
            self.black_moves = 0
            self.current_player = "white"

    def reset(self, initial_state: Optional[str] = None) -> None:
        if initial_state:
            self._parse_state(initial_state)
        else:
            self.white_position = 0
            self.black_position = 0
            self.white_speed = 0
            self.black_speed = 0
            self.white_moves = 0
            self.black_moves = 0
        self.current_player = "white"

    def get_state(self) -> str:
        """Return state as string"""
        return f"{self.white_position}:{self.white_speed}:{self.white_moves}|{self.black_position}:{self.black_speed}:{self.black_moves}|{self.current_player}"

    def legal_moves(self) -> List[str]:
        """
        Return legal moves:
        - 'accelerate': Increase speed by 1 (max speed: 10)
        - 'maintain': Keep current speed
        - 'boost': Increase speed by 3 (costs 2 moves)
        """
        if self.is_game_over():
            return []

        current_speed = self.white_speed if self.current_player == "white" else self.black_speed
        current_moves = self.white_moves if self.current_player == "white" else self.black_moves

        # If current player has used all moves, no legal moves
        if current_moves >= self.MAX_MOVES:
            return []

        moves = ["maintain"]

        if current_speed < 10:
            moves.append("accelerate")

        # Boost available if player has at least 2 moves left
        if current_speed < 8 and (current_moves < self.MAX_MOVES - 1):
            moves.append("boost")

        return moves

    def is_game_over(self) -> bool:
        """Game ends when both reach finish or both run out of moves"""
        # Check if someone crossed finish line
        if self.white_position >= self.TRACK_LENGTH or self.black_position >= self.TRACK_LENGTH:
            return True

        # Check if both ran out of moves
        if self.white_moves >= self.MAX_MOVES and self.black_moves >= self.MAX_MOVES:
            return True

        return False

    def result(self) -> Dict[str, str]:
        """Get game result - winner is who finishes first or goes furthest"""
        if not self.is_game_over():
            return {"status": "ongoing", "result": "*"}

        # Check who finished
        white_finished = self.white_position >= self.TRACK_LENGTH
        black_finished = self.black_position >= self.TRACK_LENGTH

        if white_finished and black_finished:
            # Both finished, compare moves taken (fewer is better)
            if self.white_moves < self.black_moves:
                return {"status": "win", "winner": "white", "result": "White wins (faster)"}
            elif self.black_moves < self.white_moves:
                return {"status": "win", "winner": "black", "result": "Black wins (faster)"}
            else:
                return {"status": "draw", "result": "1/2-1/2 (tie)"}
        elif white_finished:
            return {"status": "win", "winner": "white", "result": "White wins (finished)"}
        elif black_finished:
            return {"status": "win", "winner": "black", "result": "Black wins (finished)"}
        else:
            # Neither finished, compare positions
            if self.white_position > self.black_position:
                return {"status": "win", "winner": "white", "result": "White wins (further)"}
            elif self.black_position > self.white_position:
                return {"status": "win", "winner": "black", "result": "Black wins (further)"}
            else:
                return {"status": "draw", "result": "1/2-1/2 (tie)"}

    def push_move(self, move: str) -> bool:
        """Apply a move"""
        move = move.strip().lower()

        if move not in self.legal_moves():
            return False

        if self.current_player == "white":
            if move == "accelerate":
                self.white_speed = min(10, self.white_speed + 1)
                self.white_moves += 1
            elif move == "boost":
                self.white_speed = min(10, self.white_speed + 3)
                self.white_moves += 2
            elif move == "maintain":
                self.white_moves += 1

            # Move forward based on speed
            self.white_position += self.white_speed

            # Switch turn only if other player hasn't used all moves
            if self.black_moves < self.MAX_MOVES and not self.is_game_over():
                self.current_player = "black"
        else:
            if move == "accelerate":
                self.black_speed = min(10, self.black_speed + 1)
                self.black_moves += 1
            elif move == "boost":
                self.black_speed = min(10, self.black_speed + 3)
                self.black_moves += 2
            elif move == "maintain":
                self.black_moves += 1

            # Move forward based on speed
            self.black_position += self.black_speed

            # Switch turn only if other player hasn't used all moves
            if self.white_moves < self.MAX_MOVES and not self.is_game_over():
                self.current_player = "white"

        return True

    def get_turn(self) -> str:
        """Get current player"""
        return self.current_player
