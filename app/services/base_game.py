from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Dict, Optional


class BaseGameEngine(ABC):
    """Abstract base class for all game engines"""
    
    @abstractmethod
    def reset(self, initial_state: Optional[str] = None) -> None:
        """Reset the game to initial or given state"""
        pass
    
    @abstractmethod
    def get_state(self) -> str:
        """Get current game state as a string representation"""
        pass
    
    @abstractmethod
    def legal_moves(self) -> List[str]:
        """Return list of legal moves in standardized format"""
        pass
    
    @abstractmethod
    def is_game_over(self) -> bool:
        """Check if game is over"""
        pass
    
    @abstractmethod
    def result(self) -> Dict[str, str]:
        """Get game result: status, winner, result string"""
        pass
    
    @abstractmethod
    def push_move(self, move: str) -> bool:
        """Apply a move. Returns True if legal, False otherwise"""
        pass






















