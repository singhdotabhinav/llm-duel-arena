import pytest

from app.models.base import RandomFallbackAdapter
from app.services.chess_engine import ChessEngine


@pytest.mark.asyncio
async def test_random_fallback_produces_legal_move():
    eng = ChessEngine()
    adapter = RandomFallbackAdapter("random")
    move, err = await adapter.get_move(eng)
    assert err is None
    assert move in eng.legal_moves_uci()






















