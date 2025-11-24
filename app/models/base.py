from __future__ import annotations

import abc
import random
from typing import Optional, Dict, Tuple

from ..services.chess_engine import ChessEngine
from ..core.config import settings


class ModelAdapter(abc.ABC):
    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        self.tokens_used: int = 0

    @abc.abstractmethod
    async def get_move(self, engine: ChessEngine) -> Tuple[Optional[str], Optional[str]]:
        """Return (uci_move, error). Implementations must produce a legal UCI move or an error message."""
        raise NotImplementedError


class RandomFallbackAdapter(ModelAdapter):
    async def get_move(self, engine: ChessEngine) -> Tuple[Optional[str], Optional[str]]:
        legal = engine.legal_moves_uci()
        if not legal:
            return None, "no legal moves"
        return random.choice(legal), None


def parse_model_uri(uri: str) -> Tuple[str, str]:
    if ":" in uri:
        provider, name = uri.split(":", 1)
    else:
        provider, name = "ollama", uri
    return provider, name


def get_adapter(uri: str) -> ModelAdapter:
    provider, name = parse_model_uri(uri)
    if provider == "openai":
        from .openai_adapter import OpenAIAdapter

        if not settings.openai_api_key:
            return RandomFallbackAdapter(name)
        return OpenAIAdapter(name)
    if provider == "anthropic":
        from .anthropic_adapter import AnthropicAdapter

        if not settings.anthropic_api_key:
            return RandomFallbackAdapter(name)
        return AnthropicAdapter(name)
    if provider == "local":
        from .local_hf_adapter import LocalHFAdapter

        if not settings.enable_local_model:
            return RandomFallbackAdapter(name)
        return LocalHFAdapter(name)
    if provider == "ollama":
        from .ollama_adapter import OllamaAdapter

        return OllamaAdapter(name)
    if provider == "hf":
        from .huggingface_adapter import HuggingFaceAdapter
        
        return HuggingFaceAdapter(name)
    return RandomFallbackAdapter(name)
