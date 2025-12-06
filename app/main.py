from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from .core.config import settings
from .core.logging import configure_logging
from .routers import games
from .middleware.security import setup_cors, setup_rate_limiting, add_security_headers, error_handler_middleware

configure_logging()

app = FastAPI(title=settings.app_name, debug=settings.debug if settings.is_local else False)  # Disable debug in production

# IMPORTANT: Middleware order matters! Add in reverse order of execution
# 1. Error handler (outermost - catches all errors)
error_handler_middleware(app)

# 2. Security headers
add_security_headers(app)

# 3. CORS (after security headers but before auth)
setup_cors(app, cors_origins=settings.cors_origins)

# 4. Rate limiting
if settings.enable_rate_limiting:
    setup_rate_limiting(app)

# 5. Session middleware (must be after rate limiting, before routers)
# Configure session cookies based on deployment mode
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    session_cookie="session",
    max_age=3600,  # 1 hour (increased for OAuth flow)
    same_site="lax",
    https_only=(not settings.is_local),  # True in production, False in local development
    path="/",
    # CRITICAL: Don't set domain parameter at all
    # Starlette will automatically set domain=None which allows cookie for localhost
    # Explicitly setting domain=None might cause issues, so we omit it
)


app.mount("/static", StaticFiles(directory=str(settings.static_dir)), name="static")
templates = Jinja2Templates(directory=str(settings.templates_dir))

app.include_router(games.router, prefix="/api/games", tags=["games"])

# Use Cognito for authentication
if settings.use_cognito:
    # Use OIDC-based Cognito auth (using authlib)
    from .routers import cognito_oidc_auth

    app.include_router(cognito_oidc_auth.router, prefix="/auth", tags=["auth"])

    # Also include the programmatic auth endpoints (signup/login forms) for direct API access
    from .routers import cognito_auth

    app.include_router(cognito_auth.router, prefix="/api/auth", tags=["auth-api"])
else:
    raise RuntimeError(
        "Cognito authentication is required. Set USE_COGNITO=true in your environment variables."
    )


@app.get("/", response_class=HTMLResponse)
async def landing(request: Request):
    user = request.session.get("user")
    return templates.TemplateResponse(
        "landing.html",
        {
            "request": request,
            "app_name": settings.app_name,
            "use_cognito": settings.use_cognito,
            "user": user,
        },
    )


@app.get("/game", response_class=HTMLResponse)
async def game(request: Request, game_id: str = None):
    # Determine which template to serve based on game type
    template_name = "index.html"

    game_type_param = request.query_params.get("game_type") if not game_id else None
    if game_type_param == "racing":
        template_name = "racing.html"
    elif game_type_param == "word_association_clash":
        template_name = "word_association.html"

    if game_id:
        # Fetch game state to determine game type
        from .services.game_manager import game_manager

        state = game_manager.get_state(game_id)
        if state and state.game_type == "racing":
            template_name = "racing.html"
        elif state and state.game_type == "word_association_clash":
            template_name = "word_association.html"

    return templates.TemplateResponse(
        template_name,
        {
            "request": request,
            "app_name": settings.app_name,
            "default_white": settings.default_white_model,
            "default_black": settings.default_black_model,
        },
    )


@app.get("/games", response_class=HTMLResponse)
async def games_list(request: Request):
    return templates.TemplateResponse(
        "games_list.html",
        {
            "request": request,
            "app_name": settings.app_name,
            "use_cognito": settings.use_cognito,
        },
    )


@app.get("/my-games", response_class=HTMLResponse)
async def my_games(request: Request):
    return templates.TemplateResponse(
        "my_games.html",
        {
            "request": request,
            "app_name": settings.app_name,
            "use_cognito": settings.use_cognito,
        },
    )


@app.get("/favicon.ico")
async def favicon():
    return RedirectResponse(url="/static/favicon.svg")


@app.get("/auth/login-page", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page for Cognito auth"""
    if not settings.use_cognito:
        return RedirectResponse(url="/auth/login", status_code=302)
    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "app_name": settings.app_name,
        },
    )


@app.get("/auth/signup-page", response_class=HTMLResponse)
async def signup_page(request: Request):
    """Signup page for Cognito auth"""
    if not settings.use_cognito:
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse(
        "signup.html",
        {
            "request": request,
            "app_name": settings.app_name,
        },
    )
