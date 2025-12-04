"""
Pydantic schemas for game-related API requests
Provides input validation and security controls
"""

from typing import Optional, List
from pydantic import BaseModel, Field, validator
import re


# Whitelist of allowed model providers and patterns
ALLOWED_MODEL_PREFIXES = ["ollama:", "openai:", "anthropic:", "huggingface:"]

# Maximum lengths for security
MAX_MODEL_NAME_LENGTH = 100
MAX_GAME_TYPE_LENGTH = 50
MAX_MOVE_LENGTH = 20


class GameCreateRequest(BaseModel):
    """Request to create a new game"""

    game_type: str = Field(..., min_length=1, max_length=MAX_GAME_TYPE_LENGTH, description="Type of game to create")
    white_model: str = Field(..., min_length=1, max_length=MAX_MODEL_NAME_LENGTH, description="Model for white player")
    black_model: str = Field(..., min_length=1, max_length=MAX_MODEL_NAME_LENGTH, description="Model for black player")

    @validator("game_type")
    def validate_game_type(cls, v):
        """Validate game type against whitelist"""
        allowed_types = ["chess", "tic_tac_toe", "rock_paper_scissors", "racing", "word_association_clash"]
        if v not in allowed_types:
            raise ValueError(f"Invalid game type. Allowed: {allowed_types}")
        return v

    @validator("white_model", "black_model")
    def validate_model_name(cls, v):
        """Validate model name against whitelist prefixes"""
        # Check if model starts with an allowed prefix
        if not any(v.startswith(prefix) for prefix in ALLOWED_MODEL_PREFIXES):
            raise ValueError(f"Invalid model name. Must start with one of: {ALLOWED_MODEL_PREFIXES}")

        # Additional sanitization - no special characters except : and -
        if not re.match(r"^[a-zA-Z0-9:._-]+$", v):
            raise ValueError("Model name contains invalid characters. Only alphanumeric, :, ., _, - allowed")

        return v


class MoveRequest(BaseModel):
    """Request to make a move in a game"""

    move: str = Field(..., min_length=1, max_length=MAX_MOVE_LENGTH, description="Move to make")

    @validator("move")
    def sanitize_move(cls, v):
        """Sanitize move input"""
        # Remove any leading/trailing whitespace
        v = v.strip()

        # For safety, ensure no special characters that could cause issues
        # Allow alphanumeric, basic chess notation, and common separators
        if not re.match(r"^[a-zA-Z0-9\s\-+=x]+$", v):
            raise ValueError("Move contains invalid characters")

        return v


class AutoplayRequest(BaseModel):
    """Request to start autoplay mode"""

    speed: Optional[float] = Field(default=1.0, ge=0.1, le=10.0, description="Speed multiplier for autoplay (0.1 to 10.0)")


class RandomDuelRequest(BaseModel):
    """Request to create a random duel game"""

    game_type: Optional[str] = Field(
        default="chess", max_length=MAX_GAME_TYPE_LENGTH, description="Type of game for random duel"
    )

    @validator("game_type")
    def validate_game_type(cls, v):
        """Validate game type against whitelist"""
        if v is None:
            return "chess"

        allowed_types = ["chess", "tic_tac_toe", "rock_paper_scissors", "racing", "word_association_clash"]
        if v not in allowed_types:
            raise ValueError(f"Invalid game type. Allowed: {allowed_types}")
        return v
