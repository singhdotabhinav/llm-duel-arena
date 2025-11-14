# LLM Duel Arena

A web-based platform for LLM-vs-LLM competitions in turn-based two-player games. Supports multiple game types including Chess, Tic Tac Toe, Rock Paper Scissors, and Sprint Racing with real-time visualization and pluggable model backends (OpenAI GPT, Anthropic Claude, and local models via Transformers or Ollama).

## Features

- 🎮 **Multiple Games**: Chess, Tic Tac Toe, Rock Paper Scissors, Sprint Racing, Word Association Clash
- 🔐 **Google Sign-In**: Track your games and view your battle history
- 🎨 **Animated UI**: Beautiful racing animations and real-time game visualization
- 🤖 **Multiple LLM Backends**: Ollama (local), OpenAI, Anthropic, HuggingFace
- 💾 **Game History**: All your games are saved to your account

## Quickstart

1. Create and activate a virtual environment.
2. Copy `env.example` to `.env` and configure:
   - **Required**: Set `APP_SECRET_KEY` to a random 32+ character string
   - **Optional**: Configure Google OAuth for user authentication (see below)
3. Install deps: `pip install -r requirements.txt`.
4. Ensure Ollama is running locally (`ollama serve`).
5. Pull models you want to use, e.g.:
   - `ollama pull llama3.1`
   - `ollama pull mistral-nemo`
6. Run: `uvicorn app.main:app --reload`.
7. Open http://localhost:8000.

Defaults are set to use two Ollama models: `ollama:llama3.1:latest` vs `ollama:mistral-nemo:latest`.

## Google Authentication Setup (Optional)

To enable user accounts and game history:

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create a new project or select existing
3. Click "Create Credentials" → "OAuth client ID"
4. Choose "Web application"
5. Add authorized redirect URI: `http://localhost:8000/auth/callback`
6. Copy Client ID and Client Secret to your `.env` file
7. Restart the server

Without Google OAuth, you can still play games, but they won't be saved to your account.

## Features
- FastAPI backend with modular services
- Multiple game engines:
  - **Chess**: Full chess implementation using python-chess
  - **Tic Tac Toe**: Classic 3x3 grid game
  - **Rock Paper Scissors**: Single-round simultaneous choice game
  - **Sprint Racing** 🏎️: Limited-move race to the finish with speed mechanics
  - **Word Association Clash** 🧠: Timed prompt duel with scoring, duplicate checks, and live history
- LLM adapters (Ollama, OpenAI, Anthropic, local HF stub)
- Match runner with validation, retries, and logging
- Jinja2 frontend with animated boards, controls, and event log
- Real-time game state updates and move visualization

## Environment
See `env.example` for configuration options. If using Ollama, cloud API keys are not required.

## Development
- Python 3.11+
- Run tests: `pytest`

## License
MIT
