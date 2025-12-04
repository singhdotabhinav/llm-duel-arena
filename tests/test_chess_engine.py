import pytest

from app.services.chess_engine import ChessEngine


def test_legal_move_and_fen_update():
    eng = ChessEngine()
    assert not eng.is_game_over()
    start_fen = eng.get_fen()
    assert eng.push_uci("e2e4")
    assert eng.get_fen() != start_fen
    # move should be illegal if repeating same move from same position now
    assert not eng.push_uci("e2e4")






















