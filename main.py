from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import FRONTEND_DIR
from app.database import init_db
from app.scheduler import shutdown_scheduler, start_scheduler
from app.routers import generation, music, series, settings, videos, voices


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    start_scheduler()
    yield
    shutdown_scheduler()


app = FastAPI(title="FacelessAI", lifespan=lifespan)

app.include_router(series.router,     prefix="/api/series",   tags=["series"])
app.include_router(videos.router,     prefix="/api/videos",   tags=["videos"])
app.include_router(settings.router,   prefix="/api/settings", tags=["settings"])
app.include_router(generation.router, prefix="/api/generate", tags=["generate"])
app.include_router(voices.router,     prefix="/api/voices",   tags=["voices"])
app.include_router(music.router,      prefix="/api/music",    tags=["music"])

app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/")
async def serve_frontend():
    return FileResponse(str(FRONTEND_DIR / "index.html"))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
