# Sprint Racing Game 🏎️

## Overview
Sprint Racing is a fast-paced, limited-move racing game where two LLMs compete to reach the finish line first. Each racer has 20 moves to travel 100 distance units, making strategic speed management crucial.

## Game Mechanics

### Track
- **Length**: 100 distance units
- **Finish Line**: First to reach or exceed 100 units wins

### Move Limit
- Each racer gets a maximum of **20 moves**
- Moves are alternating (white, black, white, black, etc.)
- Game ends when both racers use all moves OR someone crosses the finish line

### Actions

Players can choose from three actions each turn:

1. **Accelerate** 🚀
   - Cost: 1 move
   - Effect: +1 speed (max speed: 10)
   - Use: Gradual speed increase

2. **Boost** ⚡
   - Cost: 2 moves
   - Effect: +3 speed (max speed: 10)
   - Use: Quick acceleration burst
   - Limitation: Only available if you have at least 2 moves remaining

3. **Maintain** 🔄
   - Cost: 1 move
   - Effect: No speed change
   - Use: Keep current speed when already at optimal pace

### Movement
- After each action, the racer moves forward by their current speed
- Speed is maintained between turns
- Maximum speed is capped at 10 units per move

## Victory Conditions

### 1. First to Finish
If one or both racers cross the finish line (position ≥ 100):
- If only one finishes: That racer wins
- If both finish: The one who used fewer moves wins (faster time)
- If both finish with same moves: Draw

### 2. Maximum Distance (when moves run out)
If neither racer crosses the finish line after 20 moves:
- Winner is whoever went furthest
- If same distance: Draw

## Strategy Tips

### For LLMs:
- **Early acceleration** is important - start building speed quickly
- **Boost strategically** - using boost early can give a significant advantage
- **Watch the move count** - don't waste moves on maintain when at low speed
- **Calculate remaining distance** - ensure you have enough moves to reach the finish
- **Optimal strategy**: Accelerate to high speed early, then maintain

### Example Optimal Strategy:
1. Moves 1-3: Use boost and accelerate to reach speed 6-8
2. Moves 4-15: Maintain at high speed, covering ~70-80 units
3. Moves 16-20: Final accelerates to cross finish line

## Technical Implementation

### Game State
State format: `white_pos:white_speed:white_moves|black_pos:black_speed:black_moves|turn`

Example: `45:8:10|42:7:10|white`
- White: Position 45, Speed 8, 10 moves used
- Black: Position 42, Speed 7, 10 moves used
- Current turn: White

### Files
- **Engine**: `app/services/racing_engine.py`
- **Frontend**: `app/templates/racing.html`
- **JavaScript**: `app/static/js/racing.js`
- **CSS**: `app/static/css/racing.css`
- **Tests**: `tests/test_racing_engine.py`

## Animations

The racing game includes several visual effects:

1. **Vehicle Movement**: Smooth transitions as racers move forward
2. **Speed Effects**: 
   - Vehicles tilt and scale based on speed
   - Speed trail (💨) appears at high speeds
   - Glow effects on active racer
3. **Finish Effects**:
   - Victory spin animation when crossing finish line
   - Golden glow on winner
   - Checkered flag animation
4. **Lane Highlighting**: Active racer's lane glows cyan

## UI Features

- **Real-time position tracking**: Shows exact position (e.g., "Position: 45/100")
- **Speed display**: Current speed shown below each vehicle
- **Move counter**: Tracks moves used out of 20 maximum
- **Distance markers**: Track shows 0, 25, 50, 75, 100 markers
- **Action log**: Records each move with emoji indicators

## Testing

Run racing game tests:
```bash
pytest tests/test_racing_engine.py -v
```

All tests verify:
- Basic movement and speed mechanics
- Victory conditions (finish line and max distance)
- State persistence and serialization
- Move limit enforcement

## Future Enhancements

Potential additions:
- Obstacles on the track
- Power-ups (speed boost, opponent slow)
- Multiple lap races
- Different track lengths
- Weather/terrain effects on speed
- Cornering mechanics for more complex tracks









