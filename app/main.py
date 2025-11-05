from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .core.config import settings
from .routers import games

app = FastAPI(title=settings.app_name)

app.mount("/static", StaticFiles(directory=str(settings.static_dir)), name="static")
templates = Jinja2Templates(directory=str(settings.templates_dir))

app.include_router(games.router, prefix="/api/games", tags=["games"])


@app.get("/", response_class=HTMLResponse)
async def landing(request: Request):
    return templates.TemplateResponse(
        "landing.html",
        {
            "request": request,
            "app_name": settings.app_name,
        },
    )


@app.get("/game", response_class=HTMLResponse)
async def game(request: Request, game_id: str = None):
    # Determine which template to serve based on game type
    template_name = "index.html"
    
    if game_id:
        # Fetch game state to determine game type
        from .services.game_manager import game_manager
        state = game_manager.get_state(game_id)
        if state and state.game_type == "racing":
            template_name = "racing.html"
    
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
        },
    )


@app.get("/favicon.ico")
async def favicon():
    return RedirectResponse(url="/static/favicon.svg")
