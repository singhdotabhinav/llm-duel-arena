from __future__ import annotations

import json
import re
from typing import Optional, Tuple

import httpx

from ..services.chess_engine import ChessEngine
from .base import ModelAdapter

UCI_REGEX = re.compile(r"\b([a-h][1-8][a-h][1-8][qrbn]?)\b", re.IGNORECASE)
TTT_REGEX = re.compile(r"\b([0-2]\s*,\s*[0-2])\b")
RPS_REGEX = re.compile(r"\b(rock|paper|scissors|r|p|s)\b", re.IGNORECASE)


class OllamaAdapter(ModelAdapter):
    def __init__(self, model_name: str) -> None:
        super().__init__(model_name)
        self.base_url = "http://localhost:11434"

    async def get_move(self, engine) -> Tuple[Optional[str], Optional[str]]:
        # Detect game type from engine
        is_chess = hasattr(engine, "board") and hasattr(engine.board, "legal_moves")
        is_ttt = hasattr(engine, "board") and isinstance(engine.board, list)
        is_rps = hasattr(engine, "white_choice") and hasattr(engine, "black_choice")
        is_racing = hasattr(engine, "white_position") and hasattr(engine, "black_position")
        is_trivia = hasattr(engine, "history") and hasattr(engine, "current_prompt")

        if is_chess:
            legal = engine.legal_moves()
            if not legal:
                return None, "no legal moves"
            system_prompt = (
                "You are playing chess. Choose aggressive moves that maximize quick checkmate:"
                " prefer captures, checks, or strong threats. Respond with ONLY one UCI move like 'e2e4' or 'e7e8q'."
            )
            user_prompt = f"FEN: {engine.get_state()}\n" "Return only one legal move in UCI (e.g., e2e4)."
            num_predict = 8
        elif is_ttt:
            legal = engine.legal_moves()
            if not legal:
                return None, "no legal moves"
            system_prompt = (
                "You are playing Tic Tac Toe. Choose the best move strategically."
                " Respond with ONLY one move in format 'row,col' where row and col are 0, 1, or 2."
            )
            board_str = self._format_ttt_board(engine)
            user_prompt = (
                f"Current board:\n{board_str}\n" "Return only one legal move in format 'row,col' (e.g., '1,1' for center)."
            )
            num_predict = 5
        elif is_rps:
            legal = engine.legal_moves()
            if not legal:
                return None, "no legal moves"
            system_prompt = (
                "You are playing Rock Paper Scissors. Choose strategically: "
                "rock beats scissors, scissors beats paper, paper beats rock."
                " Respond with ONLY one choice: 'rock', 'paper', or 'scissors'."
            )
            opponent_choice = engine.white_choice if engine.current_player == "black" else engine.black_choice
            if opponent_choice:
                user_prompt = f"Your opponent chose: {opponent_choice}\n" "Return only one choice: rock, paper, or scissors."
            else:
                user_prompt = "First round - no opponent choice yet.\n" "Return only one choice: rock, paper, or scissors."
            num_predict = 3
        elif is_racing:
            legal = engine.legal_moves()
            if not legal:
                return None, "no legal moves"

            current_player = engine.get_turn()
            current_pos = engine.white_position if current_player == "white" else engine.black_position
            current_speed = engine.white_speed if current_player == "white" else engine.black_speed
            current_moves = engine.white_moves if current_player == "white" else engine.black_moves
            opponent_pos = engine.black_position if current_player == "white" else engine.white_position

            system_prompt = (
                "You are racing to reach position 100 first. You have 20 moves maximum. "
                "Choose the best action to win the race. "
                "Respond with ONLY one action: 'accelerate', 'boost', or 'maintain'."
            )
            user_prompt = (
                f"Current position: {current_pos}/100 | Speed: {current_speed} | Moves used: {current_moves}/20\n"
                f"Opponent position: {opponent_pos}/100\n"
                f"Legal actions: {', '.join(legal)}\n"
                "Return only one action (accelerate, boost, or maintain)."
            )
            num_predict = 4
        elif is_trivia:
            state_data = {}
            try:
                state_data = json.loads(engine.get_state())
            except Exception:
                state_data = {}
            prompt_text = state_data.get("current_prompt") or "general knowledge"
            history = state_data.get("history", [])
            current_turn = state_data.get("turn", "white")
            previous_responses = []
            for entry in history:
                if entry.get("white"):
                    previous_responses.append(f"White: {entry['white']}")
                if entry.get("black"):
                    previous_responses.append(f"Black: {entry['black']}")

            system_prompt = (
                "You are playing Word Association Clash. Respond with 1-3 words that are clearly related to the prompt "
                "and different from every previous response. Avoid punctuation or explanations—just the association."
            )

            previous_text = "\n".join(previous_responses) if previous_responses else "None yet."
            user_prompt = (
                f"Prompt: {prompt_text}\n"
                f"Current side: {'White' if current_turn == 'white' else 'Black'}\n"
                f"Previous associations:\n{previous_text}\n"
                "Return ONLY a new association in 1-3 words that connects to the prompt. No explanations, just the words."
            )
            num_predict = 15  # Increased for better word association responses
        else:
            return None, "unknown game type"

        payload = {
            "model": self.model_name,
            "prompt": f"{system_prompt}\n\n{user_prompt}",
            "stream": False,
            "options": {"temperature": 0.4, "num_predict": num_predict},
        }
        try:
            # Use longer timeout for word association (longer prompts)
            timeout_seconds = 30.0 if is_trivia else 5.0
            async with httpx.AsyncClient(timeout=timeout_seconds) as client:
                resp = await client.post(f"{self.base_url}/api/generate", json=payload)
                if resp.status_code == 404 and self.model_name.endswith(":latest"):
                    fallback_model = self.model_name.rsplit(":", 1)[0]
                    fallback_payload = dict(payload)
                    fallback_payload["model"] = fallback_model
                    resp = await client.post(f"{self.base_url}/api/generate", json=fallback_payload)
                try:
                    resp.raise_for_status()
                except httpx.HTTPStatusError as exc:
                    detail = exc.response.text.strip()
                    if detail:
                        return None, f"ollama {exc.response.status_code}: {detail}"
                    return None, f"ollama {exc.response.status_code}: {exc!s}"

            data = resp.json()
            content = (data.get("response") or "").strip()

            # Track token usage from Ollama response
            if "prompt_eval_count" in data:
                self.tokens_used += data.get("prompt_eval_count", 0)
            if "eval_count" in data:
                self.tokens_used += data.get("eval_count", 0)

            if is_chess:
                move = self._extract_uci(content)
                if move in legal:
                    return move, None
                compact = re.sub(r"[^a-h1-8qrbn]", "", content.lower())
                if compact in legal:
                    return compact, None
            elif is_ttt:
                move = self._extract_ttt(content)
                if move in legal:
                    return move, None
            elif is_rps:
                move = self._extract_rps(content)
                if move in legal:
                    return move, None
            elif is_racing:
                move = self._extract_racing(content)
                if move in legal:
                    return move, None
            elif is_trivia:
                move = self._extract_trivia(content)
                if move:
                    return move, None
                # If extraction failed, try to use the first few words directly
                cleaned = content.strip().replace("\n", " ").replace("\r", " ")
                tokens = cleaned.split()
                if tokens:
                    # Take first 3 words as fallback
                    fallback_move = " ".join(tokens[:3]).strip().strip(",.;:!?")
                    if fallback_move:
                        return fallback_move, None
                return None, f"could not extract association from: {content[:50]}"

            return None, f"illegal or unparsed move: {content}"
        except Exception as e:
            return None, str(e)

    def _extract_uci(self, text: str) -> Optional[str]:
        m = UCI_REGEX.search(text)
        if m:
            return m.group(1).lower()
        return None

    def _extract_ttt(self, text: str) -> Optional[str]:
        m = TTT_REGEX.search(text)
        if m:
            parts = m.group(1).split(",")
            return f"{parts[0].strip()},{parts[1].strip()}"
        return None

    def _format_ttt_board(self, engine) -> str:
        """Format TTT board for LLM prompt"""
        board = engine.board
        rows = []
        for i, row in enumerate(board):
            cells = []
            for j, cell in enumerate(row):
                if cell == "X":
                    cells.append("X")
                elif cell == "O":
                    cells.append("O")
                else:
                    cells.append(f"{i},{j}")
            rows.append(" | ".join(cells))
        return "\n".join(rows)

    def _extract_rps(self, text: str) -> Optional[str]:
        """Extract RPS choice from text"""
        m = RPS_REGEX.search(text.lower())
        if m:
            choice = m.group(1).lower()
            # Map short forms to full forms
            if choice == "r":
                return "rock"
            elif choice == "p":
                return "paper"
            elif choice == "s":
                return "scissors"
            return choice
        return None

    def _extract_racing(self, text: str) -> Optional[str]:
        """Extract racing action from text"""
        text = text.lower().strip()
        if "boost" in text:
            return "boost"
        elif "accelerate" in text or "accel" in text:
            return "accelerate"
        elif "maintain" in text or "keep" in text:
            return "maintain"
        return None

    def _extract_trivia(self, text: str) -> Optional[str]:
        """Extract trivia association: use a concise fragment."""
        cleaned = text.strip().replace("\n", " ")
        if not cleaned:
            return None
        tokens = cleaned.split()
        if not tokens:
            return None
        trimmed = " ".join(tokens[:3])
        return trimmed.strip().strip(",.;:")
