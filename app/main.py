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
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "app_name": settings.app_name,
            "default_white": settings.default_white_model,
            "default_black": settings.default_black_model,
        },
    )


@app.get("/favicon.ico")
async def favicon():
    return RedirectResponse(url="/static/favicon.svg")
