import pytest
from app.services.racing_engine import RacingEngine


def test_racing_engine_basic():
    """Test basic racing engine functionality"""
    engine = RacingEngine()
    
    # Initial state
    assert engine.white_position == 0
    assert engine.black_position == 0
    assert engine.white_speed == 0
    assert engine.black_speed == 0
    assert engine.get_turn() == 'white'
    assert not engine.is_game_over()
    
    # Test accelerate
    assert 'accelerate' in engine.legal_moves()
    assert engine.push_move('accelerate')
    assert engine.white_speed == 1
    assert engine.white_position == 1
    assert engine.get_turn() == 'black'
    
    # Black accelerate
    assert engine.push_move('accelerate')
    assert engine.black_speed == 1
    assert engine.black_position == 1
    
    # Test maintain
    assert engine.push_move('maintain')
    assert engine.white_speed == 1
    assert engine.white_position == 2  # Moved at speed 1
    
    # Test boost
    assert 'boost' in engine.legal_moves()
    assert engine.push_move('boost')
    assert engine.black_speed == 4  # Was 1, boosted by 3
    assert engine.black_position == 5  # Moved at speed 4
    assert engine.black_moves == 3  # Boost costs 2 moves


def test_racing_finish_condition():
    """Test race finish condition"""
    engine = RacingEngine()
    
    # Accelerate to max speed and reach finish
    for _ in range(10):  # Get to speed 10
        engine.push_move('accelerate')
        if engine.get_turn() == 'white':
            engine.push_move('accelerate')
    
    # Keep moving at speed 10 until someone finishes
    while not engine.is_game_over() and engine.white_position < 100:
        if engine.white_moves < 20:
            engine.push_move('maintain')
        if not engine.is_game_over() and engine.black_moves < 20:
            engine.push_move('maintain')
    
    assert engine.is_game_over()
    result = engine.result()
    assert result['status'] in ['win', 'draw']


def test_racing_state_persistence():
    """Test state save/load"""
    engine = RacingEngine()
    
    # Make some moves
    engine.push_move('accelerate')
    engine.push_move('boost')
    
    # Save state
    state = engine.get_state()
    
    # Create new engine with saved state
    engine2 = RacingEngine(state)
    
    assert engine2.white_position == engine.white_position
    assert engine2.white_speed == engine.white_speed
    assert engine2.white_moves == engine.white_moves
    assert engine2.black_position == engine.black_position
    assert engine2.black_speed == engine.black_speed
    assert engine2.black_moves == engine.black_moves
    assert engine2.get_turn() == engine.get_turn()


def test_racing_max_moves_limit():
    """Test that game ends after max moves"""
    engine = RacingEngine()
    
    # Play max moves for both players without finishing
    for _ in range(20):
        if engine.white_moves < 20:
            engine.push_move('maintain')
        if engine.black_moves < 20:
            engine.push_move('maintain')
    
    assert engine.is_game_over()
    result = engine.result()
    # Winner is whoever went furthest
    assert result['status'] in ['win', 'draw']


def test_racing_cannot_exceed_max_moves():
    """Test that players cannot make moves beyond the 20-move limit"""
    engine = RacingEngine()
    
    # Play until both players have used all moves (alternating)
    move_count = 0
    max_iterations = 100  # Safety limit
    while move_count < max_iterations and not engine.is_game_over():
        current_moves = engine.white_moves if engine.get_turn() == 'white' else engine.black_moves
        if current_moves < 20:
            result = engine.push_move('maintain')
            if result:
                move_count += 1
        else:
            # Player has reached max moves, should have no legal moves
            assert len(engine.legal_moves()) == 0
            # Try to force a move - should fail
            assert not engine.push_move('maintain')
            break
    
    # Game should be over when both reach 20 moves
    assert engine.is_game_over()
    assert engine.white_moves == 20
    assert engine.black_moves == 20
    
    # Verify neither player can move anymore
    original_turn = engine.get_turn()
    assert len(engine.legal_moves()) == 0
    assert not engine.push_move('maintain')
    
    # Verify move counters haven't changed
    assert engine.white_moves == 20
    assert engine.black_moves == 20

