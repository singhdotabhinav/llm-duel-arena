from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass
from typing import Dict, Optional

import chess

from .game_manager import game_manager
from ..models.base import get_adapter
from ..core.config import settings


@dataclass
class ControlState:
    running: bool = False
    paused: bool = False
    task: Optional[asyncio.Task] = None
    white_model: Optional[str] = None
    black_model: Optional[str] = None
    tokens_used: int = 0


class MatchRunner:
    def __init__(self) -> None:
        self._controls: Dict[str, ControlState] = {}

    def get_control(self, game_id: str) -> ControlState:
        if game_id not in self._controls:
            self._controls[game_id] = ControlState()
        return self._controls[game_id]

    def start(self, game_id: str, white_model: str, black_model: str) -> None:
        ctrl = self.get_control(game_id)
        ctrl.white_model = white_model
        ctrl.black_model = black_model
        ctrl.running = True
        ctrl.paused = False
        if ctrl.task and not ctrl.task.done():
            return
        ctrl.task = asyncio.create_task(self._run_loop(game_id))

    def pause(self, game_id: str) -> None:
        ctrl = self.get_control(game_id)
        ctrl.paused = True

    def resume(self, game_id: str) -> None:
        ctrl = self.get_control(game_id)
        ctrl.paused = False

    def stop(self, game_id: str) -> None:
        ctrl = self.get_control(game_id)
        ctrl.running = False
        ctrl.paused = False

    async def _run_loop(self, game_id: str) -> None:
        ctrl = self.get_control(game_id)
        state = game_manager.get_state(game_id)
        if not state:
            return
        white = get_adapter(ctrl.white_model or state.white_model or settings.default_white_model)
        black = get_adapter(ctrl.black_model or state.black_model or settings.default_black_model)
        retry_limit = settings.move_retry_limit
        token_budget = settings.token_budget_per_match
        consecutive_failures = 0
        max_consecutive_failures = 5

        while True:
            await asyncio.sleep(0.1)
            if not ctrl.running:
                return
            if ctrl.paused:
                await asyncio.sleep(0.3)
                continue

            st = game_manager.get_state(game_id)
            if not st or st.over:
                ctrl.running = False
                # Save final state
                if st:
                    from .game_db_service import save_game_to_db
                    save_game_to_db(st)
                return

            engine = game_manager._engines[game_id]
            adapter = white if st.turn == "white" else black
            if ctrl.tokens_used >= token_budget:
                game_manager.push_move(game_id, "0000", model_name=adapter.model_name, error="token budget exceeded")
                ctrl.running = False
                # Save final state
                st = game_manager.get_state(game_id)
                if st:
                    from .game_db_service import save_game_to_db
                    save_game_to_db(st)
                return

            if hasattr(engine, "turn_expired") and getattr(engine, "turn_expired")():  # type: ignore[attr-defined]
                if hasattr(engine, "register_timeout"):
                    # Register timeout - the current side failed to respond in time
                    engine.register_timeout()  # type: ignore[attr-defined]
                    # Update game state to reflect the timeout
                    state = game_manager.get_state(game_id)
                    if state and state.over:
                        # Game ended due to timeout, stop the match runner
                        ctrl.running = False
                        # Save final state
                        from .game_db_service import save_game_to_db
                        save_game_to_db(state)
                        return
                ctrl.running = not engine.is_game_over()
                await asyncio.sleep(0.2)
                continue

            move = None
            error = None
            tokens_before = adapter.tokens_used
            successful_move_str = None
            
            for _ in range(retry_limit + 1):
                move_str, err = await adapter.get_move(engine)
                if move_str is None:
                    error = err or "failed to produce move"
                    await asyncio.sleep(0.1)
                    continue
                
                preview = game_manager.push_move(
                    game_id, 
                    move_str, 
                    model_name=adapter.model_name,
                    tokens_used=0  # Will be calculated after successful move
                )
                if preview and preview.moves and not preview.moves[-1].error:
                    move = move_str
                    successful_move_str = move_str
                    break
                else:
                    error = f"illegal move: {move_str}"
                    # Remove the failed move record
                    state = game_manager.get_state(game_id)
                    if state and state.moves:
                        state.moves.pop()
                    await asyncio.sleep(0.1)

            # Calculate tokens used for this move (including all retry attempts)
            tokens_this_move = max(0, adapter.tokens_used - tokens_before)
            
            # Fallback: if adapter didn't track tokens, estimate based on move complexity
            if tokens_this_move == 0 and move is not None:
                # Estimate tokens: prompt + response (rough estimate)
                # Different games have different prompt lengths
                if st.game_type == "chess":
                    tokens_this_move = 80  # Chess prompts are longer
                elif st.game_type == "tic_tac_toe":
                    tokens_this_move = 60
                elif st.game_type == "rock_paper_scissors":
                    tokens_this_move = 40
                elif st.game_type == "racing":
                    tokens_this_move = 70
                elif st.game_type == "word_association_clash":
                    tokens_this_move = 100
                else:
                    tokens_this_move = 50  # Default estimate
            
            # Update the move record and total token counts if move succeeded
            if move is not None:
                consecutive_failures = 0
                state = game_manager.get_state(game_id)
                if state and state.moves:
                    last_move = state.moves[-1]
                    move_side = last_move.side
                    
                    # Get current totals before update (they have 0 added from push_move)
                    current_white = state.white_tokens
                    current_black = state.black_tokens
                    
                    # Update move record with actual token count
                    last_move.tokens_used = tokens_this_move
                    
                    # Update total token counts: replace the 0 we added with actual tokens
                    if move_side == "white":
                        state.white_tokens = current_white + tokens_this_move
                    else:
                        state.black_tokens = current_black + tokens_this_move
                
                ctrl.tokens_used += tokens_this_move
                
                # Check if game is over after move
                if state and state.over:
                    from .game_db_service import save_game_to_db
                    save_game_to_db(state)

            if move is None:
                consecutive_failures += 1
                if consecutive_failures >= max_consecutive_failures:
                    ctrl.running = False
                    # Force save state as aborted/error if possible, or just save current state
                    state = game_manager.get_state(game_id)
                    if state:
                        # Mark as over if not already? Or just save what we have.
                        # Ideally we'd mark it as aborted, but for now just saving ensures we don't lose it.
                        from .game_db_service import save_game_to_db
                        save_game_to_db(state)
                    return

                if hasattr(engine, "force_failure"):
                    engine.force_failure(error or "no-response")  # type: ignore[attr-defined]
                    state = game_manager.get_state(game_id)
                    if engine.is_game_over():
                        ctrl.running = False
                        # Save final state
                        if state:
                            from .game_db_service import save_game_to_db
                            save_game_to_db(state)
                else:
                    # Only use fallback for games that have legal moves (not word association)
                    legal = engine.legal_moves()
                    if legal and len(legal) > 0:
                        fallback_move = random.choice(legal)
                        game_manager.push_move(game_id, fallback_move, model_name=f"fallback:{adapter.model_name}", error=error)
                        # Check if game is over after fallback
                        state = game_manager.get_state(game_id)
                        if state and state.over:
                            from .game_db_service import save_game_to_db
                            save_game_to_db(state)
                    elif st.game_type == "word_association_clash":
                        # For word association, if we can't get a move, register a failure
                        if hasattr(engine, "force_failure"):
                            engine.force_failure(error or "no-response")
                            state = game_manager.get_state(game_id)
                            if engine.is_game_over():
                                ctrl.running = False
                                # Save final state
                                if state:
                                    from .game_db_service import save_game_to_db
                                    save_game_to_db(state)
                await asyncio.sleep(0.2)
                continue


match_runner = MatchRunner()
