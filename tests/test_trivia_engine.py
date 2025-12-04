import json

from app.services.word_association_engine import WordAssociationEngine


def _parse_state(engine: WordAssociationEngine):
    return json.loads(engine.get_state())


def test_word_association_basic_flow():
    engine = WordAssociationEngine()

    state = _parse_state(engine)
    assert state["current_prompt"] is not None
    assert engine.get_turn() == "white"

    assert engine.push_move("Lunar mission")
    assert engine.get_turn() == "black"

    assert engine.push_move("Apollo guidance")
    assert engine.get_turn() == "white"

    history = state.get("history", [])
    assert engine.scores["white"] == 1
    assert engine.scores["black"] == 1
    assert not engine.is_game_over()


def test_word_association_duplicate_response_causes_failure():
    engine = WordAssociationEngine()
    prompt = engine.current_prompt
    assert prompt

    assert engine.push_move("Ancient temples")
    assert engine.get_turn() == "black"

    # Duplicate response from black should fail and end the game in white's favour
    assert not engine.push_move("Ancient temples")
    assert engine.is_game_over()
    result = engine.result()
    assert result["winner"] == "white"
    assert engine.failure_reason == "repeat response"


def test_word_association_completion_draw():
    engine = WordAssociationEngine()
    max_rounds = engine.MAX_ROUNDS

    for idx in range(max_rounds):
        assert engine.push_move(f"White fact {idx}")
        assert engine.push_move(f"Black fact {idx}")

    assert engine.is_game_over()
    result = engine.result()
    assert result["status"] == "completed"
    assert result.get("result") in {"draw", "white wins", "black wins"}





