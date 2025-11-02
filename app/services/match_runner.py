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
                return

            engine = game_manager._engines[game_id]
            adapter = white if st.turn == "white" else black
            if ctrl.tokens_used >= token_budget:
                game_manager.push_move(game_id, "0000", model_name=adapter.model_name, error="token budget exceeded")
                ctrl.running = False
                return

            move = None
            error = None
            for _ in range(retry_limit + 1):
                uci, err = await adapter.get_move(engine)
                if uci is None:
                    error = err or "failed to produce move"
                    await asyncio.sleep(0.1)
                    continue
                preview = game_manager.push_move(game_id, uci, model_name=adapter.model_name)
                if preview and preview.moves and not preview.moves[-1].error:
                    move = uci
                    break
                else:
                    error = f"illegal move: {uci}"
                    await asyncio.sleep(0.1)

            ctrl.tokens_used += 1
            if move is None:
                # Aggressive fallback: prefer captures, then checking moves, else random
                legal_moves = list(engine.board.legal_moves)
                capture_moves = [m for m in legal_moves if engine.board.is_capture(m)]
                if capture_moves:
                    pick = random.choice(capture_moves)
                else:
                    checking_moves = []
                    for m in legal_moves:
                        engine.board.push(m)
                        if engine.board.is_check():
                            checking_moves.append(m)
                        engine.board.pop()
                    pick = random.choice(checking_moves) if checking_moves else random.choice(legal_moves) if legal_moves else None
                if pick is not None:
                    game_manager.push_move(game_id, pick.uci(), model_name=f"fallback:{adapter.model_name}", error=error)
                await asyncio.sleep(0.2)
                continue


match_runner = MatchRunner()
