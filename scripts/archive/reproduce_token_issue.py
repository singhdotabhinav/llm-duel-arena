import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from app.services.game_manager import game_manager
from app.services.match_runner import match_runner
from app.core.config import settings

# Mock settings to ensure we use a mock adapter or real one if available
# For reproduction, we can use a mock adapter that simulates token usage
from app.models.base import ModelAdapter
from typing import Tuple, Optional

class MockAdapter(ModelAdapter):
    def __init__(self, model_name: str):
        super().__init__(model_name)
        self.tokens_used = 0

    async def get_move(self, engine) -> Tuple[Optional[str], Optional[str]]:
        # Simulate token usage
        self.tokens_used += 10
        legal = engine.legal_moves()
        if legal:
            return legal[0], None
        return None, "no legal moves"

# Monkey patch get_adapter in match_runner module
import app.services.match_runner as match_runner_module

def mock_get_adapter(uri: str):
    return MockAdapter(uri)

match_runner_module.get_adapter = mock_get_adapter

async def run_test():
    print("Starting test...")
    # Create a game
    state = game_manager.create_game("tic_tac_toe", "mock:white", "mock:black")
    game_id = state.game_id
    print(f"Created game {game_id}")
    
    # Start match runner
    match_runner.start(game_id, "mock:white", "mock:black")
    
    # Wait for a few moves
    for i in range(5):
        await asyncio.sleep(1)
        state = game_manager.get_state(game_id)
        print(f"State after {i+1}s: White Tokens: {state.white_tokens}, Black Tokens: {state.black_tokens}")
        if state.over:
            break
            
    match_runner.stop(game_id)
    print("Test finished.")

if __name__ == "__main__":
    asyncio.run(run_test())
