# 🪙 Token Usage Tracking

## Overview

The LLM Duel Arena now tracks **real-time token usage** for each LLM during gameplay! Monitor costs, optimize prompts, and analyze model efficiency.

## Features

### ✨ What's Tracked

1. **Per-Move Token Counts**
   - Tokens used for each individual move
   - Displayed in game log: `Move #5: white pawn e2 → e4 [247 tokens]`

2. **Cumulative Token Totals**
   - Total tokens used by White model
   - Total tokens used by Black model
   - Live updates during gameplay

3. **Per-Model Tracking**
   - Each LLM adapter tracks its own token usage
   - Supports all providers: Ollama, OpenAI, Anthropic

4. **Database Persistence**
   - Token counts saved to database with each game
   - Historical analysis available in game history

## UI Display

### Live Token Counters

All game interfaces now show:

```
🪙 White Tokens: 1,247
🪙 Black Tokens: 1,089
```

**Locations:**
- Chess/Tic Tac Toe: Below piece counts
- Racing: Below move counters
- Updates in real-time as game progresses

### Game Log

Each move shows token usage:
```
Move #1: white pawn e2 → e4 [247 tokens]
Move #2: black pawn e7 → e5 [253 tokens]
Move #3: white knight g1 → f3 [261 tokens]
```

## Implementation Details

### Token Tracking by Provider

#### Ollama
Tracks from API response fields:
- `prompt_eval_count` - Tokens for processing prompt
- `eval_count` - Tokens for generating response

```python
if "prompt_eval_count" in data:
    self.tokens_used += data.get("prompt_eval_count", 0)
if "eval_count" in data:
    self.tokens_used += data.get("eval_count", 0)
```

#### OpenAI
Tracks from `usage` object:
- `usage.total_tokens` - Total tokens (prompt + completion)

```python
if resp.usage:
    self.tokens_used += resp.usage.total_tokens
```

#### Anthropic
Tracks from `usage` object:
- `usage.input_tokens` + `usage.output_tokens`

```python
if resp.usage:
    self.tokens_used += resp.usage.input_tokens + resp.usage.output_tokens
```

### Data Flow

```
1. LLM API Call
   ↓
2. Adapter tracks tokens from response
   ↓
3. Match runner captures tokens per move
   ↓
4. Game manager stores in MoveRecord
   ↓
5. Game state accumulates totals
   ↓
6. API returns token counts
   ↓
7. Frontend displays live counts
   ↓
8. Database saves for history
```

## Data Structures

### MoveRecord (per move)

```python
@dataclass
class MoveRecord:
    ply: int
    side: Side
    move_uci: str
    tokens_used: int = 0  # Tokens for this specific move
    # ... other fields
```

### GameState (cumulative)

```python
@dataclass
class GameState:
    game_id: str
    white_tokens: int = 0  # Total tokens used by white
    black_tokens: int = 0  # Total tokens used by black
    # ... other fields
```

### Database Schema

```sql
CREATE TABLE games (
    id STRING PRIMARY KEY,
    white_tokens INTEGER DEFAULT 0,
    black_tokens INTEGER DEFAULT 0,
    -- ... other columns
);
```

## API Response Format

### GET /api/games/{game_id}

```json
{
  "game_id": "abc123",
  "white_model": "ollama:llama3.1:latest",
  "black_model": "ollama:mistral-nemo:latest",
  "white_tokens": 1247,
  "black_tokens": 1089,
  "moves": [
    {
      "ply": 1,
      "side": "white",
      "move_uci": "e2e4",
      "tokens_used": 247,
      ...
    }
  ],
  ...
}
```

## Use Cases

### 1. Cost Monitoring

Track API costs in real-time:
- **OpenAI**: ~$0.01 per 1,000 tokens (varies by model)
- **Anthropic**: ~$0.003 per 1,000 input tokens
- **Ollama**: Free (local)

### 2. Model Efficiency Analysis

Compare models:
```
Game 1: llama3.1 used 2,341 tokens (won)
Game 2: mistral-nemo used 1,876 tokens (won)
→ mistral-nemo is more token-efficient!
```

### 3. Prompt Optimization

Identify high-token moves:
```
Move #5: [1,234 tokens] ← Why so high?
Move #6: [247 tokens] ← Normal
→ Check prompts for move #5
```

### 4. Budget Management

Token budget per match (configurable in `.env`):
```bash
TOKEN_BUDGET_PER_MATCH=20000
```

When exceeded, match automatically stops with error.

## Token Counter Styling

### Racing Game

Golden gradient counters with coin emoji:
- Background: Gold gradient with transparency
- Border: Golden glow
- Font: Monospace for numbers
- Updates: Real-time every 800ms

### Chess/Board Games

Subtle gold display below piece counts:
- Background: Light gold with transparency
- Compact inline layout
- Monospace numbers for readability

## Database Queries

### Get Total Tokens by User

```sql
SELECT 
    user_id,
    SUM(white_tokens + black_tokens) as total_tokens,
    COUNT(*) as games_played
FROM games
WHERE user_id = 'your_user_id'
GROUP BY user_id;
```

### Most Token-Intensive Games

```sql
SELECT 
    id,
    game_type,
    white_model,
    black_model,
    (white_tokens + black_tokens) as total_tokens
FROM games
ORDER BY total_tokens DESC
LIMIT 10;
```

### Average Tokens by Game Type

```sql
SELECT 
    game_type,
    AVG(white_tokens + black_tokens) as avg_tokens,
    COUNT(*) as games
FROM games
GROUP BY game_type;
```

## Configuration

### Environment Variables

```bash
# Maximum tokens per match (default: 20,000)
TOKEN_BUDGET_PER_MATCH=20000

# Request timeout (affects token counting)
REQUEST_TIMEOUT_SECONDS=30
```

### Per-Model Configuration

Adjust token limits in `app/models/*.py`:
```python
# OpenAI adapter
max_tokens=8  # Limit completion tokens

# Ollama adapter
"num_predict": num_predict  # Limit output tokens
```

## Testing

### Verify Token Tracking

1. Start a game with Ollama models
2. Watch the token counters increment
3. Check game log shows token counts per move
4. Verify totals match sum of individual moves

### Test Token Budget

1. Set low budget: `TOKEN_BUDGET_PER_MATCH=100`
2. Start a game
3. Should stop with "token budget exceeded" error
4. Verify final token counts

## Troubleshooting

### Tokens Showing as 0

**Possible causes:**
1. Using RandomFallbackAdapter (doesn't track tokens)
2. API not returning token info
3. Old game state (created before token tracking)

**Solutions:**
- Start a new game
- Check LLM API is configured correctly
- Verify adapter is tracking tokens

### Token Counts Seem Wrong

**Check:**
1. Ollama response includes `prompt_eval_count` and `eval_count`
2. OpenAI response includes `usage` object
3. Anthropic response includes `usage` object

**Debug:**
Add logging to adapter to see raw API responses

### Token Display Not Updating

**Solutions:**
1. Hard refresh browser (Ctrl+Shift+R)
2. Check browser console for JavaScript errors
3. Verify API response includes token fields

## Performance Impact

Token tracking adds:
- **Minimal overhead**: Simple integer addition
- **No API calls**: Uses existing response data
- **Efficient storage**: Integer fields in database
- **Fast rendering**: Simple DOM updates

## Future Enhancements

Potential improvements:
- [ ] Token cost calculator (estimate $ cost)
- [ ] Token usage graphs/charts
- [ ] Per-turn token analytics
- [ ] Token efficiency leaderboard
- [ ] Export token usage reports (CSV/JSON)
- [ ] Real-time cost estimation during play
- [ ] Token usage alerts/warnings
- [ ] Historical token trends

## Cost Estimation

### Example Costs (Approximate)

**OpenAI GPT-4o-mini:**
- $0.150 per 1M input tokens
- $0.600 per 1M output tokens
- Typical game: ~5,000 tokens = $0.003

**Anthropic Claude 3.5 Sonnet:**
- $3.00 per 1M input tokens
- $15.00 per 1M output tokens
- Typical game: ~5,000 tokens = $0.015

**Ollama (Local):**
- FREE! 🎉
- No token costs
- Uses local compute only

## Analytics Dashboard (Future)

Potential dashboard showing:
```
Today's Token Usage:
├─ Total: 45,234 tokens
├─ OpenAI: 12,456 tokens ($0.075)
├─ Anthropic: 8,901 tokens ($0.089)
└─ Ollama: 23,877 tokens (FREE)

Top Token Consumers:
1. llama3.1: 15,234 tokens (12 games)
2. mistral-nemo: 12,456 tokens (10 games)
3. phi3: 8,901 tokens (8 games)
```

## Summary

✅ **Implemented:**
- Real-time token tracking for all providers
- Live UI display in all games
- Per-move and cumulative counts
- Database persistence
- Game log integration
- Token budget enforcement

🎯 **Benefits:**
- Monitor API costs
- Compare model efficiency
- Optimize prompts
- Track usage history
- Budget management

Enjoy tracking your LLM token usage! 🪙🤖



