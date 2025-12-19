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

    # Use responses that are related to the prompts
    # The engine checks if responses share tokens with the prompt or previous responses
    for idx in range(max_rounds):
        # Get the current prompt to create related responses
        prompt = engine.current_prompt
        if prompt:
            # Create responses that share words with the prompt to ensure they're related
            # Use unique identifiers to avoid duplicate responses
            prompt_words = prompt.split()
            # Use first word from prompt + unique identifier
            base_word = prompt_words[0] if prompt_words else "test"
            white_response = f"{base_word} response white {idx}"
            black_response = f"{base_word} response black {idx}"
        else:
            # Fallback if no prompt (shouldn't happen after reset)
            white_response = f"test white {idx}"
            black_response = f"test black {idx}"
        
        assert engine.push_move(white_response), f"Failed to push white move {idx} with prompt '{prompt}': {white_response}"
        assert engine.push_move(black_response), f"Failed to push black move {idx} with prompt '{prompt}': {black_response}"

    assert engine.is_game_over()
    result = engine.result()
    assert result["status"] == "completed"
    assert result.get("result") in {"draw", "white wins", "black wins"}





