from __future__ import annotations

from typing import Optional, Tuple

from openai import OpenAI

from ..core.config import settings
from ..services.chess_engine import ChessEngine
from .base import ModelAdapter


SYSTEM_PROMPT = "You are playing chess. Respond with ONLY one move in UCI format like 'e2e4'. " "Do not include explanations."


class OpenAIAdapter(ModelAdapter):
    def __init__(self, model_name: str) -> None:
        super().__init__(model_name)
        self.client = OpenAI(api_key=settings.openai_api_key)

    async def get_move(self, engine: ChessEngine) -> Tuple[Optional[str], Optional[str]]:
        legal = engine.legal_moves_uci()
        if not legal:
            return None, "no legal moves"
        user_prompt = f"FEN: {engine.get_fen()}\nReturn only one legal move in UCI."
        try:
            resp = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0,
                max_tokens=8,
            )

            # Track token usage from OpenAI response
            if resp.usage:
                self.tokens_used += resp.usage.total_tokens

            content = resp.choices[0].message.content.strip()
            move = self._extract_uci(content)
            if move in legal:
                return move, None
            return None, f"illegal or unparsed move: {content}"
        except Exception as e:
            return None, str(e)

    def _extract_uci(self, text: str) -> Optional[str]:
        text = text.strip().split()[0].lower()
        if len(text) in (4, 5):
            return text
        return None
