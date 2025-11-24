"""
HuggingFace Inference API Adapter
Free tier: 30,000 requests/month
Perfect for lightweight game-playing models
"""
from __future__ import annotations

import json
import re
import os
import asyncio
from typing import Optional, Tuple

import httpx

from ..services.chess_engine import ChessEngine
from .base import ModelAdapter

UCI_REGEX = re.compile(r"\b([a-h][1-8][a-h][1-8][qrbn]?)\b", re.IGNORECASE)
TTT_REGEX = re.compile(r"\b([0-2]\s*,\s*[0-2])\b")
RPS_REGEX = re.compile(r"\b(rock|paper|scissors|r|p|s)\b", re.IGNORECASE)


class HuggingFaceAdapter(ModelAdapter):
    """
    Adapter for HuggingFace Inference API
    Free tier: 30,000 requests/month
    No infrastructure needed - they host the models!
    """
    def __init__(self, model_name: str) -> None:
        super().__init__(model_name)
        # Parse model name: hf:model-name or just model-name
        if model_name.startswith('hf:'):
            self.hf_model = model_name.replace('hf:', '')
        else:
            self.hf_model = model_name
        
        # Default to TinyLlama if not specified (fastest free model)
        if not self.hf_model or self.hf_model == 'hf':
            self.hf_model = 'TinyLlama/TinyLlama-1.1B-Chat-v1.0'
        
        # Get API token from environment
        self.api_token = os.getenv('HUGGINGFACE_API_TOKEN', '')
        self.base_url = f"https://router.huggingface.co/models/{self.hf_model}"

    async def get_move(self, engine) -> Tuple[Optional[str], Optional[str]]:
        # Detect game type from engine
        is_chess = hasattr(engine, 'board') and hasattr(engine.board, 'legal_moves')
        is_ttt = hasattr(engine, 'board') and isinstance(engine.board, list)
        is_rps = hasattr(engine, 'white_choice') and hasattr(engine, 'black_choice')
        is_racing = hasattr(engine, 'white_position') and hasattr(engine, 'black_position')
        is_trivia = hasattr(engine, 'history') and hasattr(engine, 'current_prompt')
        
        if is_chess:
            legal = engine.legal_moves()
            if not legal:
                return None, "no legal moves"
            system_prompt = (
                "You are playing chess. Choose aggressive moves that maximize quick checkmate:"
                " prefer captures, checks, or strong threats. Respond with ONLY one UCI move like 'e2e4' or 'e7e8q'."
            )
            user_prompt = (
                f"FEN: {engine.get_state()}\n"
                "Return only one legal move in UCI (e.g., e2e4)."
            )
            max_tokens = 8
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
                f"Current board:\n{board_str}\n"
                "Return only one legal move in format 'row,col' (e.g., '1,1' for center)."
            )
            max_tokens = 5
        elif is_rps:
            legal = engine.legal_moves()
            if not legal:
                return None, "no legal moves"
            system_prompt = (
                "You are playing Rock Paper Scissors. Choose strategically: "
                "rock beats scissors, scissors beats paper, paper beats rock."
                " Respond with ONLY one choice: 'rock', 'paper', or 'scissors'."
            )
            opponent_choice = engine.white_choice if engine.current_player == 'black' else engine.black_choice
            if opponent_choice:
                user_prompt = (
                    f"Your opponent chose: {opponent_choice}\n"
                    "Return only one choice: rock, paper, or scissors."
                )
            else:
                user_prompt = (
                    "First round - no opponent choice yet.\n"
                    "Return only one choice: rock, paper, or scissors."
                )
            max_tokens = 3
        elif is_racing:
            legal = engine.legal_moves()
            if not legal:
                return None, "no legal moves"
            
            current_player = engine.get_turn()
            current_pos = engine.white_position if current_player == 'white' else engine.black_position
            current_speed = engine.white_speed if current_player == 'white' else engine.black_speed
            current_moves = engine.white_moves if current_player == 'white' else engine.black_moves
            opponent_pos = engine.black_position if current_player == 'white' else engine.white_position
            
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
            max_tokens = 4
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
                "Return a new association in ≤3 words that connects to the prompt and has not been used before."
            )
            max_tokens = 6
        else:
            return None, "unknown game type"
        
        # Combine prompts for HuggingFace
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        
        try:
            headers = {"Content-Type": "application/json"}
            if self.api_token:
                headers["Authorization"] = f"Bearer {self.api_token}"
            
            payload = {
                "inputs": full_prompt,
                "parameters": {
                    "max_new_tokens": max_tokens,
                    "temperature": 0.4,
                    "return_full_text": False
                }
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(self.base_url, json=payload, headers=headers)
                
                # Handle rate limiting
                if resp.status_code == 503:
                    # Model is loading, wait and retry
                    await asyncio.sleep(5)
                    resp = await client.post(self.base_url, json=payload, headers=headers)
                
                resp.raise_for_status()
                data = resp.json()
                
                # HuggingFace returns different formats depending on model
                if isinstance(data, list) and len(data) > 0:
                    content = data[0].get('generated_text', '')
                elif isinstance(data, dict):
                    content = data.get('generated_text', '')
                else:
                    content = str(data)
                
                content = content.strip()
                
                # Track token usage (rough estimate)
                # HuggingFace doesn't always return token counts, so estimate
                self.tokens_used += len(content.split()) * 1.3  # Rough estimate
                
                # Extract move based on game type
                if is_chess:
                    move = self._extract_uci(content)
                    if move in legal:
                        return move, None
                    # Try compact version
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
                
                return None, f"illegal or unparsed move: {content}"
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                return None, "HuggingFace API rate limit exceeded. Please wait."
            return None, f"HuggingFace API error {e.response.status_code}: {e.response.text}"
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
            parts = m.group(1).split(',')
            return f"{parts[0].strip()},{parts[1].strip()}"
        return None
    
    def _format_ttt_board(self, engine) -> str:
        """Format TTT board for LLM prompt"""
        board = engine.board
        rows = []
        for i, row in enumerate(board):
            cells = []
            for j, cell in enumerate(row):
                if cell == 'X':
                    cells.append('X')
                elif cell == 'O':
                    cells.append('O')
                else:
                    cells.append(f'{i},{j}')
            rows.append(' | '.join(cells))
        return '\n'.join(rows)
    
    def _extract_rps(self, text: str) -> Optional[str]:
        """Extract RPS choice from text"""
        m = RPS_REGEX.search(text.lower())
        if m:
            choice = m.group(1).lower()
            # Map short forms to full forms
            if choice == 'r':
                return 'rock'
            elif choice == 'p':
                return 'paper'
            elif choice == 's':
                return 'scissors'
            return choice
        return None
    
    def _extract_racing(self, text: str) -> Optional[str]:
        """Extract racing action from text"""
        text = text.lower().strip()
        if 'boost' in text:
            return 'boost'
        elif 'accelerate' in text or 'accel' in text:
            return 'accelerate'
        elif 'maintain' in text or 'keep' in text:
            return 'maintain'
        return None

    def _extract_trivia(self, text: str) -> Optional[str]:
        """Extract trivia association: use a concise fragment."""
        cleaned = text.strip().replace('\n', ' ')
        if not cleaned:
            return None
        tokens = cleaned.split()
        if not tokens:
            return None
        trimmed = " ".join(tokens[:3])
        return trimmed.strip().strip(',.;:')

