from __future__ import annotations

from typing import Optional, Tuple

from ..services.chess_engine import ChessEngine
from .base import ModelAdapter, RandomFallbackAdapter


class LocalHFAdapter(RandomFallbackAdapter):
    def __init__(self, model_name: str) -> None:
        super().__init__(model_name)
        # Placeholder for future HF pipeline/vLLM client

    # Inherit random move for now






















