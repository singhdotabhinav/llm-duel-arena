from __future__ import annotations

from typing import Optional, List, Dict
from .base_game import BaseGameEngine


class RPSEngine(BaseGameEngine):
    """Rock Paper Scissors game engine"""
    
    def __init__(self, initial_state: Optional[str] = None) -> None:
        if initial_state:
            self.white_choice, self.black_choice = self._parse_state(initial_state)
        else:
            self.white_choice = None
            self.black_choice = None
        self.current_player = 'white'  # white goes first, then black
    
    def _parse_state(self, state_str: str) -> tuple[Optional[str], Optional[str]]:
        """Parse state string: format is 'white_choice,black_choice' or 'white_choice' if black hasn't chosen"""
        parts = state_str.split(',')
        white = parts[0].strip() if len(parts) > 0 and parts[0].strip() else None
        black = parts[1].strip() if len(parts) > 1 and parts[1].strip() else None
        return (white, black)
    
    def reset(self, initial_state: Optional[str] = None) -> None:
        if initial_state:
            self.white_choice, self.black_choice = self._parse_state(initial_state)
        else:
            self.white_choice = None
            self.black_choice = None
        self.current_player = 'white'
    
    def get_state(self) -> str:
        """Return state as 'white_choice,black_choice'"""
        white = self.white_choice or ''
        black = self.black_choice or ''
        return f"{white},{black}"
    
    def get_turn(self) -> str:
        """Get current player (white or black)"""
        return self.current_player
    
    def legal_moves(self) -> List[str]:
        """Return legal moves: rock, paper, scissors"""
        return ["rock", "paper", "scissors"]
    
    def push_move(self, move: str) -> bool:
        """Record player's choice"""
        move_lower = move.lower().strip()
        if move_lower not in self.legal_moves():
            return False
        
        if self.current_player == 'white':
            if self.white_choice is not None:
                return False  # Already chosen
            self.white_choice = move_lower
            self.current_player = 'black'
        else:  # black
            if self.black_choice is not None:
                return False  # Already chosen
            self.black_choice = move_lower
            self.current_player = 'white'  # Will be determined by game over check
        
        return True
    
    def is_game_over(self) -> bool:
        """Game is over when both players have chosen"""
        return self.white_choice is not None and self.black_choice is not None
    
    def result(self) -> Dict[str, str]:
        """Determine winner"""
        if not self.is_game_over():
            return {"status": "ongoing", "result": "*"}
        
        # Determine winner
        w = self.white_choice
        b = self.black_choice
        
        if w == b:
            return {"status": "draw", "result": f"Draw! Both chose {w}"}
        
        # Winning combinations: rock beats scissors, scissors beats paper, paper beats rock
        wins = {
            "rock": "scissors",
            "paper": "rock",
            "scissors": "paper"
        }
        
        if wins[w] == b:
            return {"status": "win", "winner": "white", "result": f"White wins! {w.capitalize()} beats {b}"}
        else:
            return {"status": "win", "winner": "black", "result": f"Black wins! {b.capitalize()} beats {w}"}
    
    def get_move_description(self, move_str: str, board_before_move: str) -> Dict[str, str]:
        """Get move description"""
        player = "white" if self.current_player == 'black' else "black"  # Player who just moved
        choice = move_str.lower()
        return {
            "description": f"{player} chose {choice}",
            "from_square": None,
            "to_square": None,
            "captured_piece": None,
        }

