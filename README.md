# LLM Duel Arena

A web-based platform for LLM-vs-LLM competitions in turn-based two-player games. MVP supports Chess with real-time visualization and pluggable model backends (OpenAI GPT, Anthropic Claude, and local models via Transformers or Ollama).

## Quickstart

1. Create and activate a virtual environment.
2. Copy `env.example` to `.env` (optional) and adjust as needed.
3. Install deps: `pip install -r requirements.txt`.
4. Ensure Ollama is running locally (`ollama serve`).
5. Pull models you want to use, e.g.:
   - `ollama pull llama3.1`
   - `ollama pull mistral-nemo`
6. Run: `uvicorn app.main:app --reload`.
7. Open http://localhost:8000.

Defaults are set to use two Ollama models: `ollama:llama3.1` vs `ollama:mistral-nemo`.

## Features (MVP)
- FastAPI backend with modular services
- Chess engine using python-chess
- LLM adapters (Ollama, OpenAI, Anthropic, local HF stub)
- Match runner with validation, retries, and logging
- Jinja2 frontend with board, controls, and event log

## Environment
See `env.example` for configuration options. If using Ollama, cloud API keys are not required.

## Development
- Python 3.11+
- Run tests: `pytest`

## License
MIT
