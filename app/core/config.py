import os
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings(BaseModel):
    app_name: str = os.getenv("APP_NAME", "LLM Duel Arena")
    debug: bool = os.getenv("APP_DEBUG", "true").lower() == "true"
    secret_key: str = os.getenv("APP_SECRET_KEY", "change_me")

    base_dir: Path = Path(__file__).resolve().parents[2]
    templates_dir: Path = base_dir / "app" / "templates"
    static_dir: Path = base_dir / "app" / "static"
    
    # Google OAuth
    google_client_id: str = os.getenv("GOOGLE_CLIENT_ID", "")
    google_client_secret: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    google_redirect_uri: str = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/callback")

    # Models
    default_white_model: str = os.getenv("DEFAULT_WHITE_MODEL", "ollama:llama3.1")
    default_black_model: str = os.getenv("DEFAULT_BLACK_MODEL", "ollama:mistral-nemo")

    # OpenAI
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # Anthropic
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    anthropic_model: str = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest")

    # Local
    local_model_id: str = os.getenv("LOCAL_MODEL_ID", "meta-llama/Llama-3.1-8B-Instruct")
    enable_local_model: bool = os.getenv("ENABLE_LOCAL_MODEL", "false").lower() == "true"

    # Redis
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Runtime
    request_timeout_seconds: int = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "30"))
    move_retry_limit: int = int(os.getenv("MOVE_RETRY_LIMIT", "2"))
    token_budget_per_match: int = int(os.getenv("TOKEN_BUDGET_PER_MATCH", "20000"))


settings = Settings()
