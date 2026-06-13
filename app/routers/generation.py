from datetime import datetime

import httpx
from fastapi import APIRouter, BackgroundTasks, HTTPException
from sqlmodel import Session

from app.database import engine, get_settings
from app.models import AppSettings, Series
from app.scheduler import (
    JOBS_LOCK,
    RUNNING_JOBS,
    _create_video_row,
    _run_pipeline,
)

router = APIRouter()


def _preflight_check(settings: AppSettings):
    errors = []

    if settings.script_provider == "ollama":
        try:
            r = httpx.get(f"{settings.ollama_url}/api/tags", timeout=5)
            r.raise_for_status()
        except Exception:
            errors.append(f"Ollama not reachable at {settings.ollama_url}. Run: ollama serve")

    if settings.image_provider == "local_sd":
        try:
            r = httpx.get(f"{settings.local_sd_url}/sdapi/v1/sd-models", timeout=5)
            r.raise_for_status()
        except Exception:
            errors.append(
                f"AUTOMATIC1111 not reachable at {settings.local_sd_url}. Launch with --api flag."
            )

    if settings.script_provider == "gemini" and not settings.gemini_api_key:
        errors.append("Gemini API key not set")

    if settings.script_provider == "openai" and not settings.openai_api_key:
        errors.append("OpenAI API key not set")

    if settings.voice_provider == "elevenlabs" and not settings.elevenlabs_api_key:
        errors.append("ElevenLabs API key not set")

    if settings.image_provider == "openai_images" and not settings.openai_api_key:
        errors.append("OpenAI API key not set for image generation")

    if errors:
        raise HTTPException(503, detail={"errors": errors})


@router.post("/{series_id}")
async def trigger_generation(series_id: str, background_tasks: BackgroundTasks):
    with Session(engine) as session:
        series = session.get(Series, series_id)
        if not series:
            raise HTTPException(404, "Series not found")

    with JOBS_LOCK:
        if series_id in RUNNING_JOBS:
            raise HTTPException(409, "Generation already running for this series")

    settings = get_settings()
    _preflight_check(settings)

    video_id = _create_video_row(series_id, triggered_by="manual")

    def run():
        with JOBS_LOCK:
            RUNNING_JOBS[series_id] = {
                "video_id": video_id,
                "started_at": datetime.utcnow().isoformat(),
            }
        try:
            _run_pipeline(series_id, video_id)
        except Exception:
            pass
        finally:
            with JOBS_LOCK:
                RUNNING_JOBS.pop(series_id, None)

    background_tasks.add_task(run)
    return {"video_id": video_id, "message": "Generation started"}


@router.get("/running")
def running_jobs():
    with JOBS_LOCK:
        running = [
            {"series_id": sid, "video_id": info["video_id"], "started_at": info["started_at"]}
            for sid, info in RUNNING_JOBS.items()
        ]
    return {"running": running}
