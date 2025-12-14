from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass
from typing import Any, Dict, Optional

import chess

from .game_manager import game_manager
from ..models.base import get_adapter
from ..core.config import settings


class MatchRunner:
    async def process_turn(self, game_id: str) -> Dict[str, Any]:
        """
        Process a single turn for the given game.
        Returns a dict with status info.
        """
        state = game_manager.get_state(game_id)
        if not state:
            return {"status": "error", "message": "Game not found"}

        if state.over:
            return {"status": "game_over", "result": state.result}

        # Determine current model
        current_model = None
        if state.turn == "white":
            current_model = state.white_model
        else:
            current_model = state.black_model

        if not current_model:
            return {"status": "human_turn", "message": "Waiting for human move"}

        # Check token budget
        total_tokens = state.white_tokens + state.black_tokens
        token_budget = settings.token_budget_per_match
        if total_tokens >= token_budget:
            # End game due to budget
            game_manager.push_move(game_id, "0000", model_name="system", error="token budget exceeded")
            return {"status": "game_over", "message": "Token budget exceeded"}

        # Initialize adapter
        try:
            adapter = get_adapter(current_model)
        except Exception as e:
            return {"status": "error", "message": f"Failed to load model: {e}"}

        # Reconstruct engine to check for timeouts/legal moves
        # We need to access the engine to pass to adapter.get_move
        # GameManager doesn't expose engine directly, but we can recreate it.
        # Ideally GameManager should expose a way to get engine or we duplicate creation logic.
        # Let's use GameManager's internal method if possible or just recreate.
        # GameManager._create_engine is available.
        engine = game_manager._create_engine(state.game_type, state.state)

        # Check for turn timeout (if applicable to engine)
        if hasattr(engine, "turn_expired") and getattr(engine, "turn_expired")():
            if hasattr(engine, "register_timeout"):
                engine.register_timeout()
                # We need to save this state change.
                # Since we modified engine directly, we need to manually update state in DB.
                # GameManager doesn't have a generic "update_from_engine" method exposed.
                # Let's manually update state object and save.
                state.state = engine.get_state()
                state.over = engine.is_game_over()
                state.result = engine.result()
                game_manager.db.save_state(state)

                if state.over:
                    from .game_db_service import save_game_to_db

                    # Use stored user_id from game state
                    save_game_to_db(state, state.user_id)
                return {"status": "timeout", "message": "Turn expired"}

        # Generate move
        retry_limit = settings.move_retry_limit
        move = None
        error = None
        tokens_before = adapter.tokens_used

        for _ in range(retry_limit + 1):
            move_str, err = await adapter.get_move(engine)
            if move_str is None:
                error = err or "failed to produce move"
                await asyncio.sleep(0.1)
                continue

            # Validate move by trying to push it (preview)
            # But push_move in GameManager now saves to DB! We don't want to save invalid moves.
            # We should validate against engine first.
            # Engine logic is duplicated in GameManager.push_move.
            # Let's use engine.legal_moves() to validate if possible, or clone engine.

            # Simple validation: check if move is legal in engine
            is_legal = False
            if state.game_type == "chess":
                # ChessEngine expects UCI
                if move_str in engine.legal_moves_uci():
                    is_legal = True
            elif state.game_type == "tic_tac_toe":
                if move_str in engine.legal_moves():
                    is_legal = True
            else:
                # Other games
                if move_str in engine.legal_moves():
                    is_legal = True

            if is_legal:
                move = move_str
                break
            else:
                error = f"illegal move: {move_str}"
                await asyncio.sleep(0.1)

        # Calculate tokens
        tokens_this_move = max(0, adapter.tokens_used - tokens_before)
        if tokens_this_move == 0 and move is not None:
            # Fallback token estimation
            if state.game_type == "chess":
                tokens_this_move = 80
            elif state.game_type == "tic_tac_toe":
                tokens_this_move = 60
            elif state.game_type == "rock_paper_scissors":
                tokens_this_move = 40
            elif state.game_type == "racing":
                tokens_this_move = 70
            elif state.game_type == "word_association_clash":
                tokens_this_move = 100
            else:
                tokens_this_move = 50

        print(f"[MatchRunner] Move: {move}, Tokens: {tokens_this_move}")

        if move:
            # Apply move
            new_state = game_manager.push_move(game_id, move, model_name=adapter.model_name, tokens_used=tokens_this_move)

            if new_state and new_state.over:
                from .game_db_service import save_game_to_db

                # Use stored user_id from game state
                save_game_to_db(new_state, new_state.user_id)

            return {"status": "success", "move": move}
        else:
            # Handle failure (fallback or abort)
            # We need to track consecutive failures.
            # In stateless world, we might need to store 'consecutive_failures' in GameState in DB.
            # For now, let's just try fallback immediately.

            # Fallback logic
            legal = engine.legal_moves()
            if legal and len(legal) > 0:
                fallback_move = random.choice(legal)
                game_manager.push_move(
                    game_id,
                    fallback_move,
                    model_name=f"fallback:{adapter.model_name}",
                    error=error,
                    tokens_used=tokens_this_move,
                )
                return {"status": "fallback", "move": fallback_move}
            elif state.game_type == "word_association_clash":
                if hasattr(engine, "force_failure"):
                    # Manually update tokens
                    if state.turn == "white":
                        state.white_tokens += tokens_this_move
                    else:
                        state.black_tokens += tokens_this_move

                    engine.force_failure(error or "no-response")

                    # Save state
                    state.state = engine.get_state()
                    state.over = engine.is_game_over()
                    state.result = engine.result()
                    game_manager.db.save_state(state)

                    if state.over:
                        from .game_db_service import save_game_to_db

                        # Use stored user_id from game state
                        save_game_to_db(state, state.user_id)
                    return {"status": "failure", "message": "Force failure applied"}

            return {"status": "error", "message": "Failed to produce move and no fallback available"}


match_runner = MatchRunner()
