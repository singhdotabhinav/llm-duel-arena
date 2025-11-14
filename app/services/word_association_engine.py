from __future__ import annotations

import json
import random
import re
import time
from typing import Dict, List, Optional

from .base_game import BaseGameEngine

STOPWORDS = {
    "the",
    "and",
    "or",
    "of",
    "in",
    "to",
    "a",
    "an",
    "for",
    "with",
    "by",
    "on",
    "from",
    "at",
    "over",
    "about",
}


def _normalize_text(text: str) -> str:
    tokens = re.findall(r"[a-zA-Z]+", text.lower())
    return " ".join(tokens)


def _token_set(text: str) -> set[str]:
    tokens = {token for token in re.findall(r"[a-zA-Z]+", text.lower()) if token not in STOPWORDS}
    return tokens


class WordAssociationEngine(BaseGameEngine):
    PROMPTS: List[str] = [
        "Apollo program",
        "Ocean exploration",
        "Renaissance art",
        "Quantum physics",
        "Ancient Egypt",
        "Space telescopes",
        "Green technology",
        "Classic literature",
        "World cuisine",
        "Modern architecture",
        "Artificial intelligence",
        "Medical breakthroughs",
    ]

    MAX_ROUNDS = 12
    TURN_TIMEOUT = 10.0  # seconds
    MAX_RETRIES = 2

    def __init__(self, initial_state: Optional[str] = None) -> None:
        self._prompts: List[str] = []
        self.current_round: int = 0
        self.current_prompt: Optional[str] = None
        self.turn: str = "white"
        self.turn_deadline: float = time.time() + self.TURN_TIMEOUT

        self.history: List[Dict[str, Optional[str]]] = []
        self.scores: Dict[str, int] = {"white": 0, "black": 0}
        self._used_responses: set[str] = set()

        self.failure_side: Optional[str] = None
        self.failure_reason: Optional[str] = None
        self.winner: Optional[str] = None
        self.completed: bool = False

        if initial_state:
            self._load_state(initial_state)
        else:
            self.reset()

    def reset(self, initial_state: Optional[str] = None) -> None:
        if initial_state:
            self._load_state(initial_state)
            return

        self._prompts = random.sample(self.PROMPTS, k=len(self.PROMPTS))
        self.current_round = 0
        self.history = []
        self.scores = {"white": 0, "black": 0}
        self._used_responses = set()
        self.failure_side = None
        self.failure_reason = None
        self.winner = None
        self.completed = False
        self.turn = "white"
        self._prepare_next_round()

    def _prepare_next_round(self) -> None:
        if self.current_round >= self.MAX_ROUNDS or not self._prompts:
            self.current_prompt = None
            self.completed = True
            self.turn = "white"
            self.turn_deadline = time.time()
            return

        self.current_round += 1
        self.current_prompt = self._prompts.pop(0)
        self.history.append(
            {
                "round": self.current_round,
                "prompt": self.current_prompt,
                "white": None,
                "black": None,
                "white_valid": None,
                "black_valid": None,
                "white_reason": None,
                "black_reason": None,
            }
        )
        self.turn = "white"
        self._refresh_deadline()

    def _refresh_deadline(self) -> None:
        self.turn_deadline = time.time() + self.TURN_TIMEOUT

    def _current_entry(self) -> Optional[Dict[str, Optional[str]]]:
        if not self.history:
            return None
        return self.history[-1]

    def _register_valid(self, side: str, response: str) -> None:
        entry = self._current_entry()
        if not entry:
            return

        key = "white" if side == "white" else "black"
        entry[key] = response
        entry[f"{key}_valid"] = True
        entry[f"{key}_reason"] = None
        self.scores[side] += 1
        self._used_responses.add(_normalize_text(response))

    def _register_failure(self, side: str, response: Optional[str], reason: str) -> None:
        entry = self._current_entry()
        if side == "white" and entry is None:
            entry = {
                "round": self.current_round or 1,
                "prompt": self.current_prompt,
                "white": None,
                "black": None,
                "white_valid": None,
                "black_valid": None,
                "white_reason": None,
                "black_reason": None,
            }
            self.history.append(entry)

        key = "white" if side == "white" else "black"
        if entry is not None:
            if response is not None:
                entry[key] = response
            entry[f"{key}_valid"] = False
            entry[f"{key}_reason"] = reason

        self.failure_side = side
        self.failure_reason = reason
        self.winner = "black" if side == "white" else "white"
        self.turn = side
        self.turn_deadline = time.time()

    def _is_related(self, response: str) -> bool:
        prompt_tokens = _token_set(self.current_prompt or "")
        response_tokens = _token_set(response)
        if not response_tokens:
            return False

        if prompt_tokens & response_tokens:
            return True

        entry = self._current_entry()
        if entry:
            white_tokens = _token_set(entry.get("white") or "")
            black_tokens = _token_set(entry.get("black") or "")
            if white_tokens & response_tokens or black_tokens & response_tokens:
                return True

        # Allow short single tokens to pass (e.g., names) to avoid being overly strict
        return len(response_tokens) <= 2

    def push_move(self, move: str) -> bool:
        if self.is_game_over():
            return False

        response = move.strip()
        side = self.turn

        if not response:
            self._register_failure(side, response, "empty response")
            return False

        normalized = _normalize_text(response)
        if normalized in self._used_responses:
            self._register_failure(side, response, "repeat response")
            return False

        if not self._is_related(response):
            self._register_failure(side, response, "unrelated response")
            return False

        if side == "white":
            entry = self._current_entry()
            if entry is None or entry.get("white") is not None:
                entry = {
                    "round": self.current_round,
                    "prompt": self.current_prompt,
                    "white": None,
                    "black": None,
                    "white_valid": None,
                    "black_valid": None,
                    "white_reason": None,
                    "black_reason": None,
                }
                self.history.append(entry)
            entry["white_retries"] = 0
            entry["black_retries"] = entry.get("black_retries", 0)
            self._register_valid("white", response)
            self.turn = "black"
            self._refresh_deadline()
            return True

        # black's move
        entry = self._current_entry()
        if entry is None or entry.get("white") is None:
            self._register_failure("black", response, "missing white response")
            return False

        entry["black_retries"] = 0
        entry["white_retries"] = entry.get("white_retries", 0)
        self._register_valid("black", response)

        # Round complete: prepare next round
        self._prepare_next_round()
        return True

    def legal_moves(self) -> List[str]:
        return []

    def is_game_over(self) -> bool:
        return self.failure_reason is not None or self.completed

    def get_turn(self) -> str:
        return self.turn

    def turn_expired(self) -> bool:
        return time.time() > self.turn_deadline

    def register_timeout(self) -> None:
        if not self.is_game_over():
            self._register_failure(self.turn, None, "timeout")

    def force_failure(self, reason: str) -> None:
        if not self.is_game_over():
            self._register_failure(self.turn, None, reason)

    def result(self) -> Dict[str, str]:
        if not self.is_game_over():
            return {"status": "ongoing", "result": "*"}

        if self.failure_reason:
            return {
                "status": "ended",
                "winner": self.winner,
                "result": f"{self.winner} wins",
                "reason": self.failure_reason,
            }

        # Completed normally; compare scores
        if self.scores["white"] > self.scores["black"]:
            winner = "white"
        elif self.scores["black"] > self.scores["white"]:
            winner = "black"
        else:
            winner = None

        if winner:
            return {"status": "completed", "winner": winner, "result": f"{winner} wins"}
        return {"status": "completed", "result": "draw"}

    def get_state(self) -> str:
        return json.dumps(
            {
                "current_round": self.current_round,
                "max_rounds": self.MAX_ROUNDS,
                "current_prompt": self.current_prompt,
                "turn": self.turn,
                "turn_deadline": self.turn_deadline,
                "turn_timeout": self.TURN_TIMEOUT,
                "history": self.history,
                "scores": self.scores,
                "failure_side": self.failure_side,
                "failure_reason": self.failure_reason,
                "winner": self.winner,
                "remaining_prompts": self._prompts,
                "completed": self.completed,
            }
        )

    def _load_state(self, state: str) -> None:
        data = json.loads(state)
        self._prompts = data.get("remaining_prompts", list(self.PROMPTS))
        self.current_round = data.get("current_round", 0)
        self.current_prompt = data.get("current_prompt")
        self.turn = data.get("turn", "white")
        self.turn_deadline = data.get("turn_deadline", time.time() + self.TURN_TIMEOUT)
        self.history = data.get("history", [])
        self.scores = data.get("scores", {"white": 0, "black": 0})
        self.failure_side = data.get("failure_side")
        self.failure_reason = data.get("failure_reason")
        self.winner = data.get("winner")
        self.completed = data.get("completed", False)
        self._used_responses = {_normalize_text(entry.get("white", "") or "") for entry in self.history if entry.get("white")}
        self._used_responses.update(
            {_normalize_text(entry.get("black", "") or "") for entry in self.history if entry.get("black")}
        )
        if not self.completed and not self.current_prompt:
            random.shuffle(self._prompts)

