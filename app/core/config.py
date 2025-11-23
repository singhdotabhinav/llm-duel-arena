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
    
    # Google OAuth (legacy, can be removed after Cognito migration)
    google_client_id: str = os.getenv("GOOGLE_CLIENT_ID", "")
    google_client_secret: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    google_redirect_uri: str = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/callback")
    
    # AWS Cognito
    cognito_user_pool_id: str = os.getenv("COGNITO_USER_POOL_ID", "")
    cognito_client_id: str = os.getenv("COGNITO_CLIENT_ID", "")
    cognito_client_secret: str = os.getenv("COGNITO_CLIENT_SECRET", "")  # Optional, only if app client has secret
    cognito_region: str = os.getenv("COGNITO_REGION", "us-east-1")
    cognito_domain: str = os.getenv("COGNITO_DOMAIN", "")  # e.g., your-domain.auth.us-east-1.amazoncognito.com
    cognito_callback_url: str = os.getenv("COGNITO_CALLBACK_URL", "http://localhost:8000/auth/callback")
    cognito_logout_url: str = os.getenv("COGNITO_LOGOUT_URL", "http://localhost:8000/")
    cognito_scopes: str = os.getenv("COGNITO_SCOPES", "openid email profile")  # Customizable scopes
    
    # Use Cognito instead of Google OAuth
    use_cognito: bool = os.getenv("USE_COGNITO", "false").lower() == "true"
    
    # AWS Profile (optional - for boto3 if using programmatic API)
    aws_profile: str = os.getenv("AWS_PROFILE", "")  # Leave empty to use default profile
    aws_region: str = os.getenv("AWS_REGION", "")  # Override region if needed
    
    # Cognito OIDC Authority URL (auto-generated from user pool ID and region)
    @property
    def cognito_authority(self) -> str:
        """Generate Cognito OIDC authority URL"""
        return f"https://cognito-idp.{self.cognito_region}.amazonaws.com/{self.cognito_user_pool_id}"
    
    @property
    def cognito_server_metadata_url(self) -> str:
        """Generate Cognito OIDC server metadata URL"""
        return f"{self.cognito_authority}/.well-known/openid-configuration"

    # Models
    default_white_model: str = os.getenv("DEFAULT_WHITE_MODEL", "ollama:llama3.1:latest")
    default_black_model: str = os.getenv("DEFAULT_BLACK_MODEL", "ollama:mistral-nemo:latest")

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

    # Deployment mode
    deployment_mode: str = os.getenv("DEPLOYMENT_MODE", "local")  # local or aws
    api_base_url: str = os.getenv("API_BASE_URL", "")  # Override API URL (for AWS)
    
    @property
    def is_local(self) -> bool:
        """Check if running in local development mode"""
        return self.deployment_mode == "local" or not os.getenv("AWS_LAMBDA_FUNCTION_NAME")
    
    @property
    def api_url(self) -> str:
        """Get the API base URL based on deployment mode"""
        if self.api_base_url:
            return self.api_base_url.rstrip("/")
        if self.is_local:
            return "http://localhost:8000"
        # In AWS Lambda, API Gateway URL should be set via environment variable
        return os.getenv("API_GATEWAY_URL", "")


settings = Settings()
